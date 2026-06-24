"""Native Deezer source adapter used by iTuneUp download jobs.

This module deliberately keeps network, credential storage, matching and decoding
separate so callers can replace them with fakes in tests.  It never logs session
material or resolved media URLs.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import md5
from pathlib import Path
import base64
import re
import unicodedata
from typing import Iterable, Optional, Protocol
from urllib.parse import urljoin, urlparse

import requests


class DeezerError(RuntimeError):
    """A safe, user-facing Deezer pipeline failure."""


class DeezerAuthenticationError(DeezerError):
    pass


class DeezerUnavailableError(DeezerError):
    pass


class DeezerDecodeError(DeezerError):
    pass


@dataclass(frozen=True)
class DeezerSession:
    arl: str
    session_id: str
    api_token: str
    license_token: str


@dataclass(frozen=True)
class AppleTrackMetadata:
    title: str
    artist: str
    album: str = ""
    duration_seconds: Optional[int] = None


@dataclass(frozen=True)
class DeezerCandidate:
    id: int
    title: str
    artist: str
    album: str
    duration_seconds: Optional[int]
    title_version: str = ""


@dataclass(frozen=True)
class TrackMatch:
    candidate: DeezerCandidate
    score: int


class CredentialStore(Protocol):
    def get_arl(self) -> Optional[str]: ...
    def save_arl(self, arl: str) -> None: ...
    def clear(self) -> None: ...


class KeyringCredentialStore:
    SERVICE = "iTuneUp"
    ACCOUNT = "deezer-arl"

    def _keyring(self):
        try:
            import keyring
            return keyring
        except ImportError as exc:
            raise DeezerError("Secure credential storage is unavailable. Reinstall iTuneUp.") from exc

    def get_arl(self) -> Optional[str]:
        return self._keyring().get_password(self.SERVICE, self.ACCOUNT)

    def save_arl(self, arl: str) -> None:
        self._keyring().set_password(self.SERVICE, self.ACCOUNT, arl)

    def clear(self) -> None:
        try:
            self._keyring().delete_password(self.SERVICE, self.ACCOUNT)
        except Exception:
            pass


def arl_from_callback(callback_url: str) -> str:
    """Extract the ARL from dzr's Deezer desktop callback link without logging it."""
    parsed = urlparse((callback_url or '').strip())
    if parsed.scheme != 'deezer':
        raise DeezerAuthenticationError('The Deezer sign-in callback was not recognized.')
    segments = [segment for segment in parsed.path.split('/') if segment]
    if not segments or not re.fullmatch(r'[0-9a-fA-F]+', segments[0]):
        raise DeezerAuthenticationError('The Deezer sign-in callback did not contain a valid session.')
    return segments[0]


def arl_from_browser_cookie(cookie: Optional[dict]) -> str:
    """Validate the Deezer session cookie collected after a user completes login."""
    value = (cookie or {}).get('value', '')
    if not re.fullmatch(r'[0-9a-fA-F]+', value):
        raise DeezerAuthenticationError('Deezer sign-in did not create a usable session.')
    return value


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    value = re.sub(r"\b(feat(?:uring)?|ft)\.?\s+.*$", "", value)
    value = re.sub(r"[\[\(].*?[\]\)]", "", value)
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def score_candidate(track: AppleTrackMetadata, candidate: DeezerCandidate) -> int:
    title = normalize(track.title)
    candidate_title = normalize(candidate.title)
    artist = normalize(track.artist)
    candidate_artist = normalize(candidate.artist)
    if not title or not artist or not candidate_title or not candidate_artist:
        return 0
    title_score = 50 if title == candidate_title else (35 if title in candidate_title or candidate_title in title else 0)
    artist_score = 30 if artist == candidate_artist else (20 if artist in candidate_artist or candidate_artist in artist else 0)
    album_score = 10 if track.album and normalize(track.album) == normalize(candidate.album) else 0
    duration_score = 0
    if track.duration_seconds and candidate.duration_seconds:
        difference = abs(track.duration_seconds - candidate.duration_seconds)
        duration_score = 10 if difference <= 3 else (5 if difference <= 10 else 0)
    return title_score + artist_score + album_score + duration_score


class DeezerClient:
    PUBLIC_API = "https://api.deezer.com"
    GATEWAY = "https://www.deezer.com/ajax/gw-light.php"
    MINIMUM_MATCH_SCORE = 80

    def __init__(self, http: Optional[requests.Session] = None, credential_store: Optional[CredentialStore] = None):
        self.http = http or requests.Session()
        self.credentials = credential_store or KeyringCredentialStore()

    def is_connected(self) -> bool:
        return bool(self.credentials.get_arl())

    def validate_and_save(self, arl: str) -> None:
        arl = (arl or "").strip()
        if not re.fullmatch(r"[0-9a-fA-F]+", arl):
            raise DeezerAuthenticationError("The Deezer session token format is invalid.")
        self._create_session(arl)
        self.credentials.save_arl(arl)

    def clear_session(self) -> None:
        self.credentials.clear()

    def _gateway(self, method: str, arl: str, session_id: str, api_token: str, payload: Optional[dict] = None) -> dict:
        response = self.http.post(
            self.GATEWAY,
            params={"method": method, "input": 3, "api_version": "1.0", "api_token": api_token},
            headers={"Cookie": f"sid={session_id}; arl={arl}"}, json=payload or {}, timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("error"):
            raise DeezerAuthenticationError("The Deezer session is invalid or expired.")
        return data.get("results") or {}

    def _create_session(self, arl: str) -> DeezerSession:
        try:
            ping = self.http.get(self.GATEWAY, params={"method": "deezer.ping", "api_version": "1.0", "api_token": ""}, timeout=20).json()
            session_id = ping["results"]["SESSION"]
            user = self._gateway("deezer.getUserData", arl, session_id, "")
            token = user.get("checkForm")
            license_token = ((user.get("USER") or {}).get("OPTIONS") or {}).get("license_token")
            if not session_id or not token or not license_token:
                raise DeezerAuthenticationError("The Deezer session is invalid or has no download entitlement.")
            return DeezerSession(arl, session_id, token, license_token)
        except (KeyError, ValueError, requests.RequestException) as exc:
            raise DeezerAuthenticationError("Could not validate the Deezer session. Check your connection and token.") from exc

    def current_session(self) -> DeezerSession:
        arl = self.credentials.get_arl()
        if not arl:
            raise DeezerAuthenticationError("Connect an authorized Deezer account in Settings before downloading.")
        return self._create_session(arl)

    def search(self, track: AppleTrackMetadata) -> list[DeezerCandidate]:
        response = self.http.get(f"{self.PUBLIC_API}/search/track", params={"q": f'track:"{track.title}" artist:"{track.artist}"', "limit": 25}, timeout=20)
        response.raise_for_status()
        candidates = []
        for item in response.json().get("data", []):
            candidates.append(DeezerCandidate(
                id=int(item["id"]), title=item.get("title", ""), artist=(item.get("artist") or {}).get("name", ""),
                album=(item.get("album") or {}).get("title", ""), duration_seconds=item.get("duration"), title_version=item.get("title_version", ""),
            ))
        return candidates

    def match(self, track: AppleTrackMetadata) -> TrackMatch:
        matches = sorted((TrackMatch(c, score_candidate(track, c)) for c in self.search(track)), key=lambda match: match.score, reverse=True)
        if not matches or matches[0].score < self.MINIMUM_MATCH_SCORE:
            raise DeezerUnavailableError(f"No high-confidence Deezer match for '{track.title}' by {track.artist}.")
        return matches[0]

    def _track_stream_url(self, track_id: int, session: DeezerSession) -> str:
        song = self._gateway("song.getListData", session.arl, session.session_id, session.api_token, {"sng_ids": [track_id]})
        data = (song.get("data") or [])
        if not data:
            raise DeezerUnavailableError("The Deezer track is unavailable in this account or region.")
        source = (data[0].get("FALLBACK") or data[0])
        token, resolved_id = source.get("TRACK_TOKEN"), source.get("SNG_ID")
        if not token or not resolved_id:
            raise DeezerUnavailableError("Deezer could not resolve this track.")
        response = self.http.post("https://media.deezer.com/v1/get_url", json={"license_token": session.license_token, "track_tokens": [token], "media": [{"type": "FULL", "formats": [{"cipher": "BF_CBC_STRIPE", "format": "MP3_128"}]}]}, timeout=20)
        response.raise_for_status()
        entry = (response.json().get("data") or [{}])[0]
        try:
            return entry["media"][0]["sources"][0]["url"], int(resolved_id)
        except (KeyError, IndexError, TypeError) as exc:
            raise DeezerUnavailableError("The Deezer track is unavailable for this account or region.") from exc

    @staticmethod
    def _track_key(track_id: int, cbc_secret: str) -> bytes:
        digest = md5(str(track_id).encode()).hexdigest().encode()
        secret = cbc_secret.encode()
        return bytes(secret[index] ^ digest[index] ^ digest[index + 16] for index in range(16))

    def _cbc_secret(self) -> str:
        # The public web player publishes this rotating decode constant. It is fetched per job, not persisted.
        page = self.http.get("https://www.deezer.com/en/channels/explore", timeout=20).text
        script_url = re.search(r'src="([^"]*app-web[^"]*)"', page)
        if not script_url:
            raise DeezerDecodeError("Could not initialize the Deezer decoder. Please try again later.")
        script = self.http.get(urljoin('https://www.deezer.com', script_url.group(1)), timeout=20).text
        encoded = re.search(r'(%5B0x..%2C.{39}%2C0x..%5D)', script)
        if not encoded:
            raise DeezerDecodeError("Could not initialize the Deezer decoder. Please try again later.")
        values = re.findall(r"%([0-9A-Fa-f]{2})", encoded.group(1))
        chars = [chr(int(value, 16)) for value in values]
        if len(chars) < 16:
            raise DeezerDecodeError("Could not initialize the Deezer decoder. Please try again later.")
        return "".join(chars[index] for index in (7, 15, 6, 14, 5, 13, 4, 12, 3, 11, 2, 10, 1, 9, 0, 8))

    def download_mp3(self, track_id: int, destination: Path) -> None:
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        except ImportError as exc:
            raise DeezerDecodeError("Audio decoder is unavailable. Reinstall iTuneUp.") from exc
        session = self.current_session()
        url, resolved_id = self._track_stream_url(track_id, session)
        key = self._track_key(resolved_id, self._cbc_secret())
        response = self.http.get(url, stream=True, timeout=60)
        response.raise_for_status()
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with destination.open("wb") as output:
                block_index = 0
                for encrypted in response.iter_content(2048):
                    if not encrypted:
                        continue
                    if block_index % 3 == 0 and len(encrypted) == 2048:
                        decryptor = Cipher(algorithms.Blowfish(key), modes.CBC(bytes(range(8)))).decryptor()
                        output.write(decryptor.update(encrypted) + decryptor.finalize())
                    else:
                        output.write(encrypted)
                    block_index += 1
        except requests.RequestException as exc:
            destination.unlink(missing_ok=True)
            raise DeezerDecodeError("The Deezer audio download failed. Please try again.") from exc
