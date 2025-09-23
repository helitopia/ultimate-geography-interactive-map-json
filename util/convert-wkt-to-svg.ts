import * as d3 from 'd3';
import * as fs from 'fs';
import * as path from 'path';
// @ts-ignore
import parse from 'wellknown';

interface SourceMetadata {
    layerName: string;
    entityIdentifier: string;
    remark?: string;
}

interface AreaDev {
    areaWKT: string;
    sourceMetadata: SourceMetadata;
}

interface AreasDev {
    'low-res'?: AreaDev;
    'medium-res'?: AreaDev;
    'high-res'?: AreaDev;
}

interface AreaReference {
    referenceType: 'regionReference' | 'territoryReference';
    referenceId: string;
}

interface DisputedRegion {
    controlType: 'CONTROLLED' | 'CLAIMED';
    areaReference: AreaReference;
}

interface RegionDev {
    regionName: string;
    areas: AreasDev;
    disputedRegions?: DisputedRegion[];
}

interface WorldDataDev {
    commonTerritories?: Record<string, string>;
    regions: Record<string, RegionDev>;
}

interface AreaProd {
    areaSVG: string;
}

interface AreasProd {
    'low-res'?: AreaProd;
    'medium-res'?: AreaProd;
    'high-res'?: AreaProd;
}

interface RegionProd {
    regionName: string;
    areas: AreasProd;
    disputedRegions?: DisputedRegion[];
}

interface WorldDataProd {
    width: number;
    height: number;
    commonTerritories?: Record<string, string>;
    regions: Record<string, RegionProd>;
}

// SVG dimensions in 16:9 ratio
//TODO write these props in prod output json
const WIDTH = 1600;
const HEIGHT = 900;

// Create a single global projection that will be used for all countries
let globalPathGenerator: d3.GeoPath;

function initializeGlobalProjection(worldDataDev: WorldDataDev) {
    // Collect all geometries to create a bounding box for the entire world
    const allFeatures: any[] = [];

    for (const region of Object.values(worldDataDev.regions)) {
        if (region.areas?.['high-res']?.areaWKT) {
            const geojson = parse(region.areas['high-res'].areaWKT);
            if (geojson) {
                allFeatures.push(geojson);
            }
        }
    }

    // Create a FeatureCollection with all geometries
    const featureCollection: GeoJSON.FeatureCollection = {
        type: 'FeatureCollection',
        features: allFeatures.map(f => ({ type: 'Feature', geometry: f, properties: {} }))
    };

    // Create a projection fitted to the entire world
    let projection = d3.geoMercator()
        .fitSize([WIDTH, HEIGHT], featureCollection);

    globalPathGenerator = d3.geoPath().projection(projection);
}

function convertWKTToSVG(wkt: string): string {
    // Parse WKT to GeoJSON
    const geojson = parse(wkt);

    if (!geojson) {
        throw new Error(`Failed to parse WKT: ${wkt.substring(0, 100)}...`);
    }

    // Use the global path generator
    const svgPath = globalPathGenerator(geojson);

    if (!svgPath) {
        throw new Error(`Failed to generate SVG path for WKT: ${wkt.substring(0, 100)}...`);
    }

    return svgPath;
}

function convertAreaDev(areaDev: AreaDev): AreaProd {
    const svgPath = convertWKTToSVG(areaDev.areaWKT);
    return {
        areaSVG: svgPath
    };
}

function convertAreasDev(areasDev: AreasDev): AreasProd {
    return {
        // ...(areasDev['high-res'] && { 'high-res': convertAreaDev(areasDev['high-res']) }),
        'medium-res': convertAreaDev(areasDev['medium-res'])
        // ...(areasDev['low-res'] && { 'low-res': convertAreaDev(areasDev['low-res']) }),
    };
}

function convertRegionDev(regionDev: RegionDev): RegionProd {
    const regionProd: RegionProd = {
        regionName: regionDev.regionName,
        areas: convertAreasDev(regionDev.areas)
    };

    // Preserve disputedRegions if they exist
    if (regionDev.disputedRegions) {
        regionProd.disputedRegions = regionDev.disputedRegions;
    }

    return regionProd;
}

function convertWorldData(worldDataDev: WorldDataDev): WorldDataProd {
    // Initialize global projection before converting any regions
    console.log('Initializing global projection...');
    initializeGlobalProjection(worldDataDev);

    const worldDataProd: WorldDataProd = {
        width: WIDTH,
        height: HEIGHT,
        regions: {}
    };

    // Preserve commonTerritories if they exist
    if (worldDataDev.commonTerritories) {
        worldDataProd.commonTerritories = worldDataDev.commonTerritories;
    }

    // Convert all regions
    for (const [regionCode, regionDev] of Object.entries(worldDataDev.regions)) {
        console.log(`Converting region: ${regionCode} (${regionDev.regionName})`);
        if (regionCode.length > 3 || !worldDataDev.regions[regionCode].areas || worldDataDev.regions[regionCode].areas["medium-res"] === undefined) {
            console.log(`Skipping ${regionCode} region with no areas defined`);
            continue;
        }
        worldDataProd.regions[regionCode] = convertRegionDev(regionDev);
    }

    return worldDataProd;
}

function main() {
    const inputPath = path.join(__dirname, '..', 'src', 'world.json');
    const outputPath = path.join(__dirname, '..', 'src', 'world-prod.json');

    console.log(`Reading input file: ${inputPath}`);
    const inputData = fs.readFileSync(inputPath, 'utf-8');
    const worldDataDev: WorldDataDev = JSON.parse(inputData);

    console.log(`Converting ${Object.keys(worldDataDev.regions).length} regions...`);
    const worldDataProd = convertWorldData(worldDataDev);

    console.log(`Writing output file: ${outputPath}`);
    fs.writeFileSync(outputPath, JSON.stringify(worldDataProd, null, 2), 'utf-8');

    console.log('Conversion complete!');
}

main();
