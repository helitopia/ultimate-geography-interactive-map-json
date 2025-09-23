import {readFileSync} from 'fs';
import {fileURLToPath} from 'url';
import {dirname, resolve} from 'path';
import Ajv from 'ajv';
import addFormats from 'ajv-formats';

if (!process.argv[2] || !process.argv[3]) {
    console.error('Usage: node validate-schema.mjs <schema-file> <data-file>');
    process.exit(1);
}

const __dirname = dirname(fileURLToPath(import.meta.url));
const schemaPath = resolve(__dirname, process.argv[2]);
const dataPath = resolve(__dirname, process.argv[3]);

const schema = JSON.parse(readFileSync(schemaPath, 'utf8'));
const data = JSON.parse(readFileSync(dataPath, 'utf8'));

const ajv = new Ajv({allErrors: true, strict: false});
addFormats(ajv);

const validateSchema = ajv.compile(schema);
if (!validateSchema(data)) {
    console.error('Schema validation failed:');
    for (const err of validateSchema.errors) {
        console.error('-', err.instancePath || '(root)', err.message);
    }
    process.exit(1);
} else
    console.log('world.json is valid');