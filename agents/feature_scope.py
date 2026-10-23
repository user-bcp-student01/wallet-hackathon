"""Feature-scoped prompt guidance for the Crew roles."""

import unicodedata
from collections.abc import Mapping


def _normalized_title(feature: Mapping[str, object]) -> str:
    title = str(feature.get("title", "")).casefold()
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", title)
        if not unicodedata.combining(character)
    )


def is_onboarding_feature(feature: Mapping[str, object]) -> bool:
    title = _normalized_title(feature)
    if "onboard" in title:
        return True
    has_registration = any(
        term in title for term in ("registro", "registration", "alta", "sign up", "signup")
    )
    has_wallet_context = any(
        term in title for term in ("wallet", "usuario", "user", "cuenta", "account")
    )
    return has_registration and has_wallet_context


def is_payment_feature(feature: Mapping[str, object]) -> bool:
    title = _normalized_title(feature)
    return any(
        term in title
        for term in ("payment", "pago", "transfer", "qr", "reversal", "reverso")
    )


def scoped_instructions(
    feature: Mapping[str, object],
    common: str,
    *,
    onboarding: str = "",
    payment: str = "",
) -> str:
    if is_onboarding_feature(feature):
        return "\n".join(part for part in (common, onboarding) if part)
    if is_payment_feature(feature):
        return "\n".join(part for part in (common, payment) if part)
    return common
