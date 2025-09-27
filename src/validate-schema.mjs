import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';
import Ajv from 'ajv';
import addFormats from 'ajv-formats';

const __dirname = dirname(fileURLToPath(import.meta.url));
const schemaPath = resolve(__dirname, 'world.schema.json');
const dataPath = resolve(__dirname, 'world.json');

const schema = JSON.parse(readFileSync(schemaPath, 'utf8'));
const data = JSON.parse(readFileSync(dataPath, 'utf8'));

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);

const validateSchema = ajv.compile(schema);
if (!validateSchema(data)) {
    console.error('Schema validation failed:');
    for (const err of validateSchema.errors) {
        console.error('-', err.instancePath || '(root)', err.message);
    }
    process.exit(1);
}
else
    console.log('world.json is valid');