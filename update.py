import json
import os
import logging
from typing import Tuple, Dict, List, Union

import pycountry
import requests
from tqdm import tqdm

PISTON_META_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
LANGUAGES_FILE = "languages.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def get_lang_asset_root(version: str) -> str:
    """Returns the base URL for language files for a given Minecraft version."""
    return f"https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/refs/heads/{version}/assets/minecraft/lang/"


def get_latest_minecraft_version() -> str:
    """Fetches the latest official Minecraft release version from Mojang's API."""
    logging.info("Fetching latest Minecraft version...")
    return requests.get(PISTON_META_URL).json()["latest"]["release"]


def get_available_lang_files(version: str) -> List[str]:
    """Retrieves a list of available language JSON files for a given Minecraft version."""
    url = f"{get_lang_asset_root(version)}_list.json"
    logging.info(f"Fetching available language files from {url}...")
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["files"]
    raise RuntimeError(f"Failed to fetch language files for version {version}")


def get_lang_info(name: str, version: str) -> Dict[str, Union[str, Dict[str, str]]]:
    """Fetches and constructs language metadata from a specific language file."""
    url = f"{get_lang_asset_root(version)}{name}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        locale = data["language.code"]
        english_name, english_region = get_locale_details(locale)
        return {
            "iso_code": locale,
            "native": {
                "name": data["language.name"],
                "region": data["language.region"]
            },
            "english": {
                "name": english_name,
                "region": english_region
            }
        }
    raise RuntimeError(f"Failed to fetch language file {name} for version {version}")


def get_locale_details(locale: str) -> Tuple[str, str]:
    """Converts a locale string (e.g., 'de_DE') to its corresponding English language and country names."""
    parts = locale.split("_")
    if len(parts) == 2:
        lang_code, region_code = parts
        language = pycountry.languages.get(alpha_3=lang_code.lower())
        country = pycountry.countries.get(alpha_2=region_code.upper())
        lang_name = language.name if language else "?"
        country_name = country.name if country else "?"
        return lang_name, country_name
    return "?", "?"


def merge_lang_info(existing: dict, new: dict) -> dict:
    """
    Merges new language metadata with existing data, keeping:
    - original values when new is '?'
    - overridden values if marked with 'override_{field}': true
    """
    merged = existing.copy()

    for section in ["english"]:
        for field in ["name", "region"]:
            override_key = f"override_{field}"
            is_overridden = existing.get(section, {}).get(override_key, False)
            new_value = new[section][field]
            existing_value = existing.get(section, {}).get(field, "?")

            if is_overridden:
                merged[section][field] = existing_value
                merged[section][override_key] = True
            elif new_value == "?":
                merged[section][field] = existing_value
            else:
                merged[section][field] = new_value
                if override_key in existing.get(section, {}):
                    merged[section][override_key] = existing[section][override_key]

    merged["iso_code"] = new["iso_code"]
    merged["native"] = new["native"]

    return merged


def main():
    version = get_latest_minecraft_version()
    logging.info(f"Processing language data for Minecraft version: {version}")

    # Load or initialize language data
    if os.path.exists(LANGUAGES_FILE):
        with open(LANGUAGES_FILE, "r", encoding="utf-8") as f:
            languages = json.load(f)
        logging.info(f"Loaded existing {LANGUAGES_FILE}")
    else:
        languages = {}
        logging.info("No existing language file found, creating a new one.")

    files = [f for f in get_available_lang_files(version) if f.endswith(".json") and f != "deprecated.json"]

    with tqdm(files, desc="Languages", unit="lang") as progress:
        for lang_file in progress:
            key = lang_file.removesuffix(".json")

            try:
                info = get_lang_info(lang_file, version)
                progress.set_postfix_str(f"{key} ({info['iso_code']})")

                if key in languages:
                    languages[key] = merge_lang_info(languages[key], info)
                else:
                    languages[key] = info

                logging.debug(f"Processed {key}: {info['english']['name']} ({info['english']['region']})")

            except Exception as e:
                logging.warning(f"Failed to process {lang_file}: {e}")
                progress.set_postfix_str(f"{key} (error)")

    with open(LANGUAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(languages, f, indent=2, ensure_ascii=False)

    logging.info("✅ Finished updating languages.json")


if __name__ == "__main__":
    main()
