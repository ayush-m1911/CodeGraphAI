/**
 * Purpose:
 * Provides premium simulated graph datasets for demonstrations and offline states.
 *
 * Responsibilities:
 * - Define a full-scale structure hierarchy of a sample FastAPI repository (packages, modules, classes, calls).
 * - Match node attributes exactly with the backend GraphNode schema.
 *
 * Outputs:
 * - object: Simulated graph container containing lists of nodes and edges.
 */

export const mockGraph = {
  metadata: {
    repository: "tiangolo/fastapi",
    node_count: 9,
    edge_count: 8,
    additional_info: {
      resolved_symbols: 7
    }
  },
  nodes: [
    {
      id: "repositories/fastapi",
      symbol_name: "fastapi",
      qualified_name: "repositories/fastapi",
      file_path: "repositories/fastapi",
      node_type: "repository",
      type: "repository",
      parent: null,
      children: ["repositories/fastapi/fastapi"],
      docstring: "FastAPI framework codebase root path.",
      hierarchy_depth: 0
    },
    {
      id: "repositories/fastapi/fastapi",
      symbol_name: "fastapi",
      qualified_name: "repositories/fastapi/fastapi",
      file_path: "repositories/fastapi/fastapi",
      node_type: "package",
      type: "package",
      parent: "repositories/fastapi",
      children: ["repositories/fastapi/fastapi/routing.py", "repositories/fastapi/fastapi/applications.py"],
      docstring: "Core library packages folder.",
      hierarchy_depth: 1
    },
    {
      id: "repositories/fastapi/fastapi/routing.py",
      symbol_name: "routing.py",
      qualified_name: "repositories/fastapi/fastapi/routing.py",
      file_path: "repositories/fastapi/fastapi/routing.py",
      node_type: "file",
      type: "file",
      parent: "repositories/fastapi/fastapi",
      children: ["fastapi.routing.APIRouter"],
      docstring: "Contains classes and utility methods implementing route processing pipelines.",
      hierarchy_depth: 2,
      start_line: 1,
      end_line: 450
    },
    {
      id: "repositories/fastapi/fastapi/applications.py",
      symbol_name: "applications.py",
      qualified_name: "repositories/fastapi/fastapi/applications.py",
      file_path: "repositories/fastapi/fastapi/applications.py",
      node_type: "file",
      type: "file",
      parent: "repositories/fastapi/fastapi",
      children: ["fastapi.applications.FastAPI"],
      docstring: "Exposes the main FastAPI application coordinator class.",
      hierarchy_depth: 2,
      start_line: 1,
      end_line: 320
    },
    {
      id: "fastapi.routing.APIRouter",
      symbol_name: "APIRouter",
      qualified_name: "fastapi.routing.APIRouter",
      file_path: "repositories/fastapi/fastapi/routing.py",
      node_type: "class",
      type: "class",
      parent: "repositories/fastapi/fastapi/routing.py",
      children: ["fastapi.routing.APIRouter.get", "fastapi.routing.APIRouter.add_api_route"],
      signature: "class APIRouter(APIRoute)",
      docstring: "Router class representing path definitions mappings to custom endpoints.",
      hierarchy_depth: 3,
      start_line: 25,
      end_line: 180
    },
    {
      id: "fastapi.applications.FastAPI",
      symbol_name: "FastAPI",
      qualified_name: "fastapi.applications.FastAPI",
      file_path: "repositories/fastapi/fastapi/applications.py",
      node_type: "class",
      type: "class",
      parent: "repositories/fastapi/fastapi/applications.py",
      children: [],
      signature: "class FastAPI(Starlette)",
      docstring: "Main application driver initializing base ASGI routing adapters.",
      hierarchy_depth: 3,
      start_line: 12,
      end_line: 140
    },
    {
      id: "fastapi.routing.APIRouter.get",
      symbol_name: "get",
      qualified_name: "fastapi.routing.APIRouter.get",
      file_path: "repositories/fastapi/fastapi/routing.py",
      node_type: "method",
      type: "method",
      parent: "fastapi.routing.APIRouter",
      children: [],
      signature: "def get(self, path: str, response_model: Optional[Type[Any]] = None)",
      docstring: "Helper decorator function registering HTTP GET router paths.",
      hierarchy_depth: 4,
      start_line: 45,
      end_line: 60
    },
    {
      id: "fastapi.routing.APIRouter.add_api_route",
      symbol_name: "add_api_route",
      qualified_name: "fastapi.routing.APIRouter.add_api_route",
      file_path: "repositories/fastapi/fastapi/routing.py",
      node_type: "method",
      type: "method",
      parent: "fastapi.routing.APIRouter",
      children: [],
      signature: "def add_api_route(self, path: str, endpoint: Callable[..., Any])",
      docstring: "Registers a route configuration inside routing datasets.",
      hierarchy_depth: 4,
      start_line: 80,
      end_line: 110
    },
    {
      id: "fastapi.routing.GLOBAL_ROUTER",
      symbol_name: "GLOBAL_ROUTER",
      qualified_name: "fastapi.routing.GLOBAL_ROUTER",
      file_path: "repositories/fastapi/fastapi/routing.py",
      node_type: "variable",
      type: "variable",
      parent: "repositories/fastapi/fastapi/routing.py",
      children: [],
      docstring: "Module-level global variable for default application routing.",
      hierarchy_depth: 3,
      start_line: 10,
      end_line: 10
    }
  ],
  edges: [
    {
      source: "repositories/fastapi",
      target: "repositories/fastapi/fastapi",
      relation: "CONTAINS",
      source_file: "repositories/fastapi",
      destination_file: "repositories/fastapi/fastapi"
    },
    {
      source: "repositories/fastapi/fastapi",
      target: "repositories/fastapi/fastapi/routing.py",
      relation: "CONTAINS",
      source_file: "repositories/fastapi/fastapi",
      destination_file: "repositories/fastapi/fastapi/routing.py"
    },
    {
      source: "repositories/fastapi/fastapi",
      target: "repositories/fastapi/fastapi/applications.py",
      relation: "CONTAINS",
      source_file: "repositories/fastapi/fastapi",
      destination_file: "repositories/fastapi/fastapi/applications.py"
    },
    {
      source: "repositories/fastapi/fastapi/routing.py",
      target: "fastapi.routing.APIRouter",
      relation: "DEFINES",
      source_file: "repositories/fastapi/fastapi/routing.py",
      destination_file: "repositories/fastapi/fastapi/routing.py"
    },
    {
      source: "repositories/fastapi/fastapi/routing.py",
      target: "fastapi.routing.GLOBAL_ROUTER",
      relation: "DEFINES",
      source_file: "repositories/fastapi/fastapi/routing.py",
      destination_file: "repositories/fastapi/fastapi/routing.py"
    },
    {
      source: "repositories/fastapi/fastapi/applications.py",
      target: "fastapi.applications.FastAPI",
      relation: "DEFINES",
      source_file: "repositories/fastapi/fastapi/applications.py",
      destination_file: "repositories/fastapi/fastapi/applications.py"
    },
    {
      source: "fastapi.routing.APIRouter",
      target: "fastapi.routing.APIRouter.get",
      relation: "CONTAINS",
      source_file: "repositories/fastapi/fastapi/routing.py",
      destination_file: "repositories/fastapi/fastapi/routing.py"
    },
    {
      source: "fastapi.routing.APIRouter",
      target: "fastapi.routing.APIRouter.add_api_route",
      relation: "CONTAINS",
      source_file: "repositories/fastapi/fastapi/routing.py",
      destination_file: "repositories/fastapi/fastapi/routing.py"
    },
    {
      source: "fastapi.routing.APIRouter.get",
      target: "fastapi.routing.APIRouter.add_api_route",
      relation: "CALLS",
      source_file: "repositories/fastapi/fastapi/routing.py",
      destination_file: "repositories/fastapi/fastapi/routing.py",
      line: 52
    }
  ]
};
