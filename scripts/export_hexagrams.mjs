import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import ts from 'typescript';

const repoRoot = process.cwd();
const constantsPath = path.join(repoRoot, 'constants.ts');
const outPath = path.join(repoRoot, 'python_app', 'data', 'hexagrams.json');

const source = fs.readFileSync(constantsPath, 'utf8');
const transpiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
    importsNotUsedAsValues: ts.ImportsNotUsedAsValues.Remove,
    esModuleInterop: true,
  },
}).outputText;

const moduleObj = { exports: {} };
const sandbox = {
  module: moduleObj,
  exports: moduleObj.exports,
  require: (mod) => {
    if (mod === './types') {
      return {};
    }
    throw new Error(`Unsupported import while exporting hexagrams: ${mod}`);
  },
  console,
};

vm.runInNewContext(transpiled, sandbox, { filename: 'constants.js' });
const map = moduleObj.exports.HEXAGRAM_MAP;

if (!map || typeof map !== 'object') {
  throw new Error('Failed to load HEXAGRAM_MAP from constants.ts');
}

fs.writeFileSync(outPath, `${JSON.stringify(map, null, 2)}\n`, 'utf8');
console.log(`Exported ${Object.keys(map).length} hexagrams to ${outPath}`);
