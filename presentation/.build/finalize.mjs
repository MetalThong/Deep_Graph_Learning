import path from 'node:path';
import {pathToFileURL} from 'node:url';
const SKILL='C:/Users/Lenovo/.codex/plugins/cache/openai-primary-runtime/presentations/26.1011.11113/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(SKILL+'/container_tools/artifact_tool_utils.mjs'));
const tables=[2,3,4,5,7,9,11,12,14,17,18,19,20,21];
const result=await finalizePresentation({
 workspaceDir:path.resolve('..'),candidatePath:path.resolve('candidate.pptx'),finalPath:path.resolve('../output/Deep_Graph_26_Slides_Final.pptx'),
 pythonExecutable:'C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
 integrityValidatorPath:SKILL+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:SKILL+'/container_tools/inspect_presentation_layout_geometry.py',
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...tables.flatMap(n=>['--require-native-table-slide',String(n)])],
 explicitTotalSlideCount:26,requiredNativeTableOwnerSlides:tables,requiredNativeChartOwnerSlides:[19,20,23],
 materializeLiteralChartWorkbooks:true,
 fontPolicy:{basis:'design',families:['Arial','Cambria Math','Consolas']},verifyArtifactToolImport:true,receiptPath:path.resolve('validation-final.json')
});
console.log(JSON.stringify({path:result.finalPath,bytes:result.byteCount,import:result.firstPartyImport.passed,charts:result.nativeChartValidation.passed,packaging:result.chartDataPackaging??null}));
