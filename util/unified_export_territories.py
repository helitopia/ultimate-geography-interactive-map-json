import json
import uuid
from qgis.core import QgsProject, QgsVectorLayer

def export_countries_to_json(output_file=None):
    """
    Export QGIS vector layers with country data to JSON format matching world.schema.json.
    Processes three Natural Earth layers with different resolutions:
    - ne_110m_admin_0_countries (low-res)
    - ne_50m_admin_0_countries (medium-res)
    - ne_10m_admin_0_countries (high-res)

    Groups countries by 3-letter ISO code and creates areas for each resolution level.
    Only includes resolution levels that have actual geometry data.

    Args:
        output_file: Output JSON file path.

    Returns:
        dict: The exported countries data structure
    """

    # Define layer names and their resolution mappings
    layer_configs = [
        {"name": "ne_110m_admin_0_countries", "resolution": "low-res"},
        {"name": "ne_50m_admin_0_countries", "resolution": "medium-res"},
        {"name": "ne_10m_admin_0_countries", "resolution": "high-res"}
    ]

    # Initialize the result structure
    result_data = {
        "regions": {},
        "height": 180,
        "width": 360
    }

    # Process each layer
    for layer_config in layer_configs:
        layer_name = layer_config["name"]
        resolution = layer_config["resolution"]

        print(f"Processing layer: {layer_name}")

        # Get the layer by name
        layers = QgsProject.instance().mapLayersByName(layer_name)
        if not layers:
            print(f"Warning: Layer '{layer_name}' not found, skipping...")
            continue

        layer = layers[0]

        if not layer or not layer.isValid():
            print(f"Error: Layer '{layer_name}' is not valid, skipping...")
            continue

        # Check if required fields exist
        field_names = [field.name() for field in layer.fields()]
        if "ADMIN" not in field_names or "ADM0_A3" not in field_names:
            print(f"Error: Required fields 'ADMIN' and 'ADM0_A3' not found in layer '{layer_name}'")
            print(f"Available fields: {field_names}")
            continue

        # Process features in this layer
        for feature in layer.getFeatures():
            # Get field values
            admin = feature["ADMIN"]
            adm0_a3 = feature["ADM0_A3"]

            # Skip if no country code
            if not adm0_a3:
                continue

            # Get geometry as WKT
            geometry = feature.geometry()
            wkt = geometry.asWkt() if geometry and not geometry.isEmpty() else ""

            if not wkt:
                print(f"Warning: No geometry for {admin} ({adm0_a3}) in {layer_name}")
                continue

            # Initialize country entry if it doesn't exist
            if adm0_a3 not in result_data["regions"]:
                result_data["regions"][adm0_a3] = {
                    "regionName": admin,
                    "areas": {}
                }

            # Add the specific resolution data only if we have valid WKT
            result_data["regions"][adm0_a3]["areas"][resolution] = {
                "areaWKT": wkt,
                "sourceMetadata": {
                    "layerName": layer_name,
                    "entityIdentifier": f"ADMIN={admin}"
                }
            }

    # Clean up empty areas and remove countries with no valid geometries
    countries_to_remove = []
    for country_code, country_data in result_data["regions"].items():
        if not country_data["areas"]:
            countries_to_remove.append(country_code)

    for country_code in countries_to_remove:
        del result_data["regions"][country_code]
        print(f"Removed {country_code} - no valid geometries found")

    # Export to JSON only if output_file is specified
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            print(f"Successfully exported {len(result_data['regions'])} countries to {output_file}")
        except Exception as e:
            print(f"Error writing to file: {e}")
            return None

    # Print summary of what was processed
    resolutions_found = set()
    for country_code, country_data in result_data["regions"].items():
        for res in country_data["areas"].keys():
            resolutions_found.add(res)

    print(f"Successfully processed {len(result_data['regions'])} countries")
    print(f"Resolutions processed: {', '.join(sorted(resolutions_found))}")

    return result_data

def match_territories(countries_data=None, territory_names_file=None, output_file=None):
    """
    Match territories from territory names file with countries data
    and create a consolidated JSON output.

    Args:
        countries_data: Dictionary of countries data (if None, loads from file)
        territory_names_file: Path to territory names file
        output_file: Output JSON file path

    Returns:
        dict: The matched territories data
    """

    # Set default paths if not provided
    if territory_names_file is None:
        territory_names_file = r"C:/Users/iharkusha/Desktop/Personal/UG/Selected Notes.txt"
    if output_file is None:
        output_file = r"C:/Users/iharkusha/Desktop/matched_territories.json"

    # Read territory names
    try:
        with open(territory_names_file, 'r', encoding='utf-8') as f:
            territory_names = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(territory_names)} territory names")
    except Exception as e:
        print(f"Error reading territory names file: {e}")
        return None

    # Use provided countries_data or load from file
    if countries_data is None:
        countries_json_file = r"C:/Users/iharkusha/Desktop/countries_export.json"
        try:
            with open(countries_json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract the regions from the JSON structure
            if "regions" in data:
                countries_data = data["regions"]
            else:
                countries_data = data  # Fallback for old format

            print(f"Loaded {len(countries_data)} countries from JSON")
        except Exception as e:
            print(f"Error reading countries JSON file: {e}")
            return None
    else:
        # If countries_data is provided, extract regions if it's in the full format
        if "regions" in countries_data:
            countries_data = countries_data["regions"]

    # Create lookup dictionary for faster matching (case-insensitive)
    region_lookup = {}
    for country_code, country_info in countries_data.items():
        region_name = country_info.get("regionName", "").lower()
        if region_name:
            region_lookup[region_name] = (country_code, country_info)

    # Result structure matching the schema
    matched_result = {
        "regions": {},
        "height": 180,
        "width": 360
    }
    matched_count = 0
    unmatched_count = 0

    # Process each territory name
    for territory_name in territory_names:
        territory_lower = territory_name.lower()

        # Check if territory matches any region name
        if territory_lower in region_lookup:
            # Found match - use original country code and data
            country_code, country_info = region_lookup[territory_lower]

            # Create a deep copy of country_info to modify
            country_data = {
                "regionName": country_info["regionName"],
                "areas": {}
            }

            # Copy areas, but only if they have valid areaWKT
            if "areas" in country_info:
                for res_level, res_data in country_info["areas"].items():
                    if res_data.get("areaWKT", "").strip():
                        country_data["areas"][res_level] = res_data.copy()

            # Only add if we have at least one valid area
            if country_data["areas"]:
                matched_result["regions"][country_code] = country_data
                matched_count += 1
                print(f"Matched: {territory_name} -> {country_code}")
            else:
                print(f"Skipped {territory_name} -> {country_code} (no valid geometries)")
        else:
            # No match found - create entry with random UUID but no geometry data
            random_id = str(uuid.uuid4())
            matched_result["regions"][random_id] = {
                "regionName": territory_name,
                "areas": {
                    # Only include high-res as empty placeholder since it's most likely to be required
                    "low-res": {
                        "areaWKT": "",
                        "sourceMetadata": {
                            "layerName": "ne_110m_admin_0_countries",
                            "entityIdentifier": "ADMIN="
                        }
                    },
                    "medium-res": {
                        "areaWKT": "",
                        "sourceMetadata": {
                            "layerName": "ne_50m_admin_0_countries",
                            "entityIdentifier": "ADMIN="
                        }
                    },
                    "high-res": {
                        "areaWKT": "",
                        "sourceMetadata": {
                            "layerName": "ne_10m_admin_0_countries",
                            "entityIdentifier": "ADMIN="
                        }
                    }
                }
            }
            unmatched_count += 1
            print(f"No match: {territory_name} -> {random_id}")

    # Sort the results - 3-letter codes first (alphabetically), then UUIDs
    def sort_key(item):
        key = item[0]
        # If key is exactly 3 characters (country codes), sort first with the key itself
        if len(key) == 3:
            return (0, key)
        # UUIDs and other keys go last, sorted alphabetically
        else:
            return (1, key)

    sorted_items = sorted(matched_result["regions"].items(), key=sort_key)
    matched_result["regions"] = dict(sorted_items)

    # Write output JSON
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(matched_result, f, indent=2, ensure_ascii=False)

        print(f"\nExport completed successfully!")
        print(f"Output file: {output_file}")
        print(f"Total territories processed: {len(territory_names)}")
        print(f"Matched territories: {matched_count}")
        print(f"Unmatched territories: {unmatched_count}")

    except Exception as e:
        print(f"Error writing output file: {e}")
        return None

    return matched_result

def run_full_pipeline(territory_names_file=None, final_output_file=None):
    """
    Run the complete pipeline: export countries from QGIS layers, then match with territories.
    Only outputs the final matched territories file.

    Args:
        territory_names_file: Path to territory names file
        final_output_file: Final matched territories output file
    """

    # Set default paths
    if final_output_file is None:
        final_output_file = "C:/Users/iharkusha/Desktop/matched_territories.json"

    print("=== Step 1: Exporting countries from QGIS layers ===")
    countries_data = export_countries_to_json(output_file=None)  # Don't write intermediate file

    if countries_data is None:
        print("Failed to export countries data")
        return False

    print(f"\n=== Step 2: Matching territories ===")
    matched_result = match_territories(
        countries_data=countries_data,
        territory_names_file=territory_names_file,
        output_file=final_output_file
    )

    if matched_result is None:
        print("Failed to match territories")
        return False

    print(f"\n=== Pipeline completed successfully ===")
    print(f"Countries exported: {len(countries_data['regions'])}")
    print(f"Final territories: {len(matched_result['regions'])}")
    return True


run_full_pipeline()