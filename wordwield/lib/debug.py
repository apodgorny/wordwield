import debugpy

print('Waiting to attach debugger')
debugpy.listen(("localhost", 5678))
debugpy.wait_for_client()
debugpy.breakpoint()