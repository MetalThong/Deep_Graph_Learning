import path from 'node:path';
import {pathToFileURL} from 'node:url';

const SKILL='C:/Users/Lenovo/.codex/plugins/cache/openai-primary-runtime/presentations/26.1013.11914/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(SKILL+'/container_tools/artifact_tool_utils.mjs'));
const tables=[11,15,16,19,27,29,30,31];
const result=await finalizePresentation({
  workspaceDir:path.resolve('..'),
  candidatePath:path.resolve('combined-candidate.pptx'),
  finalPath:path.resolve('../output/Deep_Graph_Traffic_Bitcoin_32_Slides.pptx'),
  pythonExecutable:'C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
  integrityValidatorPath:SKILL+'/container_tools/inspect_presentation_package_integrity.py',
  layoutValidatorPath:SKILL+'/container_tools/inspect_presentation_layout_geometry.py',
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...tables.flatMap(n=>['--require-native-table-slide',String(n)])],
  explicitTotalSlideCount:32,
  requiredNativeTableOwnerSlides:tables,
  requiredNativeChartOwnerSlides:[19,27],
  materializeLiteralChartWorkbooks:true,
  fontPolicy:{basis:'design',families:['Arial']},
  verifyArtifactToolImport:true,
  receiptPath:path.resolve('combined-validation.json')
});
console.log(JSON.stringify({path:result.finalPath,bytes:result.byteCount,import:result.firstPartyImport.passed,charts:result.nativeChartValidation.passed,packaging:result.chartDataPackaging??null}));
