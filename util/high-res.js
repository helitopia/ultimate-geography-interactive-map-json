const fs = require('fs');
const path = require('path');

const inputPath = path.join("src", "world.json");
const outputPath = path.join("src", 'world-high-res.json');

const data = JSON.parse(fs.readFileSync(inputPath, 'utf8'));

for (const regionCode in data.regions) {
    const region = data.regions[regionCode];
    if (region.areas && region.areas['high-res']) {
        region.areas = { 'high-res': region.areas['high-res'] };
    }
}

fs.writeFileSync(outputPath, JSON.stringify(data, null, 2));
console.log(`Transformed JSON saved to: ${outputPath}`);