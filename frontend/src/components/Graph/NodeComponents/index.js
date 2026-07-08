import RepositoryNode from './RepositoryNode';
import PackageNode from './PackageNode';
import ModuleNode from './ModuleNode';
import ClassNode from './ClassNode';
import FunctionNode from './FunctionNode';
import MethodNode from './MethodNode';
import VariableNode from './VariableNode';
import ConfigurationNode from './ConfigurationNode';

export const nodeTypes = {
  repository: RepositoryNode,
  package: PackageNode,
  file: ModuleNode,
  module: ModuleNode,
  class: ClassNode,
  function: FunctionNode,
  method: MethodNode,
  variable: VariableNode,
  configuration: ConfigurationNode,
  config: ConfigurationNode
};

export {
  RepositoryNode,
  PackageNode,
  ModuleNode,
  ClassNode,
  FunctionNode,
  MethodNode,
  VariableNode,
  ConfigurationNode
};
