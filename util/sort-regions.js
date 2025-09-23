const fs = require('fs');

// Read world.json
const data = JSON.parse(fs.readFileSync('src/world.json', 'utf8'));

// Separate 3-character keys from longer keys
const threeCharKeys = [];
const longerKeys = [];

Object.keys(data.regions).forEach(key => {
  if (key.length === 3) {
    threeCharKeys.push(key);
  } else {
    longerKeys.push(key);
  }
});

// Sort each group alphabetically
threeCharKeys.sort();
longerKeys.sort();

// Combine: 3-char keys first, then longer keys
const sortedKeys = [...threeCharKeys, ...longerKeys];

// Build sorted regions object
const sortedRegions = sortedKeys.reduce((acc, key) => {
  acc[key] = data.regions[key];
  return acc;
}, {});

// Replace regions with sorted version
data.regions = sortedRegions;

// Write back to world.json
fs.writeFileSync('src/world.json', JSON.stringify(data, null, 2), 'utf8');

console.log('Regions sorted successfully!');
console.log(`3-character keys: ${threeCharKeys.length}`);
console.log(`Longer keys: ${longerKeys.length}`);
console.log(`Total regions: ${sortedKeys.length}`);
