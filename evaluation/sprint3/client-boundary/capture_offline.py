import argparse,http.server,json,threading,subprocess,pathlib
parser=argparse.ArgumentParser(description='Offline Codex inventory probe; localhost only, no credentials or inference')
parser.add_argument('output',type=pathlib.Path)
root=parser.parse_args().output.resolve()
root.mkdir(parents=True,exist_ok=False)
home=root/'home';home.mkdir(exist_ok=True)
work=root/'work';work.mkdir(exist_ok=True)
class Handler(http.server.BaseHTTPRequestHandler):
 def do_POST(self):
  body=self.rfile.read(int(self.headers.get('Content-Length',0)))
  (root/'request.json').write_bytes(body)
  (root/'request-meta.json').write_text(json.dumps({'path':self.path,'authorization_present':bool(self.headers.get('Authorization'))}))
  self.send_response(400);self.end_headers();self.wfile.write(b'{"error":{"message":"offline capture; inference unavailable"}}')
 def log_message(self,*a):pass
server=http.server.HTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
flags=['shell_tool','unified_exec','browser_use','computer_use','apps','plugins','remote_plugin','multi_agent','multi_agent_v2','view_image','image_generation','goals','memories','hooks','skill_search','tool_suggest','shell_snapshot','context_management','sleep_tool','in_app_browser','code_mode','code_mode_only','code_mode_host','incremental_tools','enable_request_compression']
args=['/opt/homebrew/bin/codex','exec','--ignore-user-config','--ignore-rules','--skip-git-repo-check','--ephemeral','--json','-m','gpt-6.1-sol','-C',str(work),'-s','read-only','-c','model_provider="offline"','-c','model_providers.offline.name="offline"','-c',f'model_providers.offline.base_url="http://127.0.0.1:{server.server_port}"','-c','model_providers.offline.wire_api="responses"','-c','model_providers.offline.requires_openai_auth=false','-c','model_providers.offline.request_max_retries=0','-c','model_providers.offline.stream_max_retries=0','-c','model_providers.offline.supports_websockets=false','-c','web_search="disabled"','-c','tools.update_plan.enabled=false','-c','tools.experimental_request_user_input.enabled=false','-c','project_doc_max_bytes=0']
for flag in flags:args+=['--disable',flag]
args+=['Offline tool-inventory capture. No actual inference.']
(root/'command.json').write_text(json.dumps(args,indent=2))
env={'PATH':'/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin','HOME':str(home),'CODEX_HOME':str(home),'TMPDIR':str(root),'CODEX_ROLLOUT_TRACE_ROOT':str(root/'traces')}
try:
 p=subprocess.run(args,cwd=work,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=40)
 (root/'stdout.txt').write_text(p.stdout);(root/'stderr.txt').write_text(p.stderr)
 print('exit',p.returncode);print(p.stderr[-3500:]);print(p.stdout[-2000:])
except subprocess.TimeoutExpired as e: print('timeout',str(e))
finally:server.shutdown()
if (root/'request.json').exists():
 body=json.loads((root/'request.json').read_text());print('REQUEST KEYS',list(body));inventory=[x for x in body.get('input',[]) if x.get('type')=='additional_tools']; (root/'request-tools.json').write_text(json.dumps(inventory,indent=2)+'\n'); print('TOOLS',json.dumps(inventory,indent=2)[:12000])
