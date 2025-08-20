import os
import sys
from time import sleep

# Ensure project root is on sys.path when running this file directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rollback_portocal import ToolRollbackRegistry, ToolSpec
if __name__ == "__main__":

    registry = ToolRollbackRegistry()

    def create_file(args):
        path = args["path"]
        open(path, "w").close()
        return {"path": path}

    def delete_file(args, result):
        path = result["path"]
        import os
        if os.path.exists(path):
            os.remove(path)

    registry.register_tool(ToolSpec(name="create_file", forward=create_file, reverse=delete_file))

        
    result = create_file({"path":"a.txt"})
    registry.record_invocation("create_file", {"path":"a.txt"}, result, success=True)
    print(registry.get_track())
    #print(sleep(10))
    registry.rollback() 
    #registry.redo()     
   