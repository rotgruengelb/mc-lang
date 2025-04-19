# Minecraft Language Metadata
This project provides language metadata for Minecraft. 

Metadata is stored in a `languages.json` file and includes native and English names for each language and region.
It uses `pycountry` to provide English names for languages and regions. The data is manually cleaned and standardized.

## Automation
The project is set up to automatically update the `languages.json` file and commit changes, if there are any, daily.

## Contributing
If you notice incorrect data in the `english.name`, `english.region` or `note` fields, please create an issue or pull request.
if you change `english.name` or `english.region` add `"override_region": true`/`"override_name": true` to the language entry in `languages.json` to indicate that the name or region has been overridden.

## Dependencies
Available in `requirements.txt`

# License
This project has multiple licenses. See [LICENSE.md](LICENSE.md) for more information.