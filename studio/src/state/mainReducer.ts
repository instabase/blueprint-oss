import {v4 as uuidv4} from 'uuid';

import * as RecordTargets from 'studio/foundation/recordTargets';
import * as Entity from 'studio/foundation/entity';
import * as TargetAssignment from 'studio/foundation/targetAssignment';
import * as TargetValue from 'studio/foundation/targetValue';
import * as Targets from 'studio/foundation/targets';
import * as TargetsSchema from 'studio/foundation/targetsSchema';

import * as MergeNode from 'studio/blueprint/mergeNode';
import * as Model from 'studio/blueprint/model';
import * as Node from 'studio/blueprint/node';
import * as PatternNode from 'studio/blueprint/patternNode';
import * as PickBestNode from 'studio/blueprint/pickBestNode';
import * as Rule from 'studio/blueprint/rule';

import * as RecordRun from 'studio/state/recordRun';
import * as ModelRun from 'studio/state/modelRun';
import * as Project from 'studio/state/project';
import * as Resource from 'studio/state/resource';
import * as Settings from 'studio/state/settings';

import assert from 'studio/util/assert';
import {UUID} from 'studio/util/types';

export type Action = {
  type: 'SetProject';
  project: Project.t;
} | {
  type: 'Undo';
} | {
  type: 'Redo';
} | {
  type: 'SetSelectedRecordName';
  recordName: string;
} | {
  type: 'SetSelectedNode';
  path: Model.Path;
} | {
  type: 'SetSelectedRule';
  path: Model.Path;
  rule: Rule.t;
} | {
  type: 'DeleteTargetsForDoc';
  recordName: string;
} | {
  type: 'AddTargetsToDoc';
  recordName: string;
} | {
  type: 'ImportTargets';
  targets: Targets.t;
} | {
  type: 'AddFieldToTargetsSchema';
  field: string;
} | {
  type: 'DeleteFieldFromTargetsSchema';
  field: string;
} | {
  type: 'SetSelectedField';
  field: string | undefined;
} | {
  type: 'SetTargetValue',
  recordName: string;
  field: string;
  value: TargetValue.t | undefined;
} | {
  type: 'ClearModel';
} | {
  type: 'PlaceIntoMerge';
  path: Model.Path;
} | {
  type: 'PlaceIntoPickBest';
  path: Model.Path;
} | {
  type: 'AddChildNode';
  parentNode: Node.WithChildren;
  parentNodePath: Model.Path;
  childNode: Node.t;
  setChildToSelectedNode: boolean;
} | {
  type: 'DeleteNode';
  path: Model.Path;
} | {
  type: 'RenameNode';
  path: Model.Path;
  name: string | undefined;
} | {
  type: 'ReplaceNodeContents';
  path: Model.Path;
  newNode: Node.t;
} | {
  type: 'AddFields';
  node: PatternNode.t;
  path: Model.Path;
  fields: [string, Entity.Type][];
} | {
  type: 'RemoveField';
  node: PatternNode.t;
  path: Model.Path;
  field: string;
} | {
  type: 'RenameField';
  node: PatternNode.t;
  path: Model.Path;
  oldName: string;
  newName: string;
} | {
  type: 'SetFieldType';
  field: string;
  newType: Entity.Type;
  isLabel: boolean;
} | {
  type: 'AddRule';
  node: Node.t;
  path: Model.Path;
  rule: Rule.t;
} | {
  type: 'RemoveRule';
  node: Node.t;
  path: Model.Path;
  rule: Rule.t;
} | {
  type: 'ReplaceRule';
  node: Node.t;
  path: Model.Path;
  oldRule: Rule.t;
  newRule: Rule.t;
} | {
  type: 'ScheduleModelRun';
  modelIndex: number;
  recordNames: string[];
  pin: boolean;
} | {
  type: 'CancelModelRun';
  uuid: UUID;
} | {
  type: 'UpdateModelRun';
  uuid: UUID;
  keep: boolean;
  pin: boolean;
} | {
  type: 'UpdateModelRecordRun';
  modelIndex: number;
  recordRun: RecordRun.t;
} | {
  type: 'ChangeSettings';
  changes: Partial<Settings.t>;
} | {
  type: 'ToggleAnnotationMode';
} | {
  type: 'Hack_UpdateProject';
  changes: Partial<Project.t>;
};

// Implementations
// ===============

function SetProject(
  _: Project.t,
  project: Project.t):
    Project.t
{
  return project;
}

function setModelIndex(
  project: Project.t,
  newIndex: number):
    Project.t
{
  const newModel = project.modelStack[newIndex];

  return {
    ...project,
    currentModelIndex: newIndex,
    selectedNodeModelPath:
      Model.maximalValidSubpath(
        newModel,
        project.selectedNodeModelPath),
    selectionMode: {type: 'None'},
    targets: {
      ...project.targets,
      schema:
        Project.syncSchemaTypes(
          newModel,
          project.targets.schema),
    },
  };
}

function Undo(project: Project.t): Project.t {
  return setModelIndex(project, project.currentModelIndex - 1);
}

function Redo(project: Project.t): Project.t {
  return setModelIndex(project, project.currentModelIndex + 1);
}

function SetSelectedRecordName(
  project: Project.t,
  recordName: string):
    Project.t
{
  return {
    ...project,
    selectedRecordName: recordName,
  };
}

function SetSelectedNode(
  project: Project.t,
  path: Model.Path):
    Project.t
{
  if (!Model.hasNode(Project.model(project), path)) {
    throw "Unknown node path";
  }

  return {
    ...project,
    selectedNodeModelPath: path,
    selectionMode: {type: 'None'},
  };
}

function SetSelectedRule(
  project: Project.t,
  path: Model.Path,
  rule: Rule.t):
    Project.t
{
  const model = Project.model(project);
  const node = Model.node(model, path) as Node.t;
  console.assert(node != undefined);
  if (!Node.hasRule(node, rule)) {
    throw "Unknown rule";
  }

  return {
    ...project,
    selectionMode: {
      type: 'Rule',
      ruleUUID: rule.uuid,
    },
  };
}

function AddTargetsToDoc(
  project: Project.t,
  recordName: string):
    Project.t
{
  return {
    ...project,
    targets: {
      ...project.targets,
      doc_targets: [
        ...project.targets.doc_targets,
        RecordTargets.build(recordName),
      ],
    },
  };
}

function ImportTargets(
  project: Project.t,
  targets: Targets.t):
    Project.t
{
  const newTargets =
    Targets.populateSchema(
      Targets.merged(
        project.targets,
        targets));
  return {
    ...project,
    targets: {
      ...newTargets,
      schema:
        Project.syncSchemaTypes(
          Project.model(project),
          newTargets.schema),
    },
  };
}

function addFieldToTargetsSchema(
  schema: TargetsSchema.t,
  field: string,
  type?: Entity.Type,
  isLabel?: boolean):
    TargetsSchema.t
{
  if (TargetsSchema.hasField(schema, field)) {
    return schema;
  } else {
    return [
      ...schema,
      {
        field,
        type: type != undefined ? type :
          Entity.heuristicDefaultType(field),
        is_label: isLabel != undefined ? isLabel :
          Entity.heuristicDefaultIsLabel(field),
      },
    ];
  }
}

function AddFieldToTargetsSchema(
  project: Project.t,
  field: string):
    Project.t
{
  if (TargetsSchema.hasField(project.targets.schema, field)) {
    throw `Attempted to add preexisting field ${field} to targets schema`;
  }

  return {
    ...project,
    targets: {
      ...project.targets,
      schema:
        addFieldToTargetsSchema(
          project.targets.schema,
          field),
    },
  };
}

function DeleteFieldFromTargetsSchema(
  project: Project.t,
  field: string):
    Project.t
{
  if (!TargetsSchema.hasField(project.targets.schema, field)) {
    throw `Attempted to delete nonexisting field ${field} from targets schema`;
  }

  return {
    ...project,
    targets: Targets.withoutField(project.targets, field),
  };
}

function DeleteTargetsForDoc(
  project: Project.t,
  recordName: string):
    Project.t
{
  return {
    ...project,
    targets: {
      ...project.targets,
      doc_targets: project.targets.doc_targets.filter(
        recordTargets => recordTargets.doc_name != recordName
      ),
    },
  };
}

function SetSelectedField(
  project: Project.t,
  field: string | undefined):
    Project.t
{
  const selectionMode: Project.SelectionMode =
    (field != undefined)
      ? {type: 'Field', field: field}
      : {type: 'None'};

  return {
    ...project,
    selectionMode,
  };
}

function SetTargetValue(
  project: Project.t,
  recordName: string,
  field: string,
  value: TargetValue.t | undefined):
    Project.t
{
  if (Project.recordTargets(project, recordName) == undefined) {
    project = AddTargetsToDoc(project, recordName);
  }

  function newAssignments(
    assignments: TargetAssignment.t[]):
      TargetAssignment.t[]
  {
    if (value == undefined) {
      return assignments.filter(assignment => assignment.field != field);
    } else if (assignments.find(
                assignment => assignment.field == field))
    {
      return assignments.map(
        assignment => {
          if (assignment.field == field) {
            return {field, value};
          } else {
            return assignment;
          }
        }
      );
    } else {
      return assignments.concat([{field, value}]);
    }
  }

  return {
    ...project,
    targets: {
      ...project.targets,
      doc_targets: project.targets.doc_targets.map(
        (entry: RecordTargets.t) => {
          if (entry.doc_name == recordName) {
            return {
              ...entry,
              assignments: newAssignments(entry.assignments),
            };
          } else {
            return entry;
          }
        },
      ),
    },
  };
}

function placeIntoNodeWithChildren(
  project: Project.t,
  path: Model.Path,
  type: 'merge' | 'pick_best'):
    Project.t
{
  const model = Project.model(project);
  const node = Model.node(model, path);
  if (node == undefined) {
    throw 'Invalid path';
  }

  const newNode = {
    type: type,
    uuid: uuidv4(),
    rules: [] as Rule.t[],
    children: [node],
  } as PickBestNode.t;
  const newModel = Model.replaceTerminusWith(model, path, newNode);
  return Project.setSelectedNode(
    Project.pushModel(project, newModel),
    path.slice(0, -1).concat([newNode.uuid]) as Model.Path);
}

function ClearModel(
  project: Project.t):
    Project.t
{
  return Project.pushModel(project, Model.build());
}

function PlaceIntoMerge(
  project: Project.t,
  path: Model.Path):
    Project.t
{
  return placeIntoNodeWithChildren(project, path, 'merge');
}

function PlaceIntoPickBest(
  project: Project.t,
  path: Model.Path):
    Project.t
{
  return placeIntoNodeWithChildren(project, path, 'pick_best');
}

function AddChildNode(
  project: Project.t,
  parentNode: Node.WithChildren,
  parentNodePath: Model.Path,
  childNode: Node.t,
  setChildToSelectedNode: boolean):
    Project.t
{
  const model = Project.model(project);
  console.assert(parentNode == Model.node(model, parentNodePath));
  const newParentNode = {
    ...parentNode,
    children: Node.children(parentNode).concat(childNode),
  };
  const newModel = Model.replaceTerminusWith(model, parentNodePath, newParentNode);

  let result = Project.pushModel(project, newModel);
  if (setChildToSelectedNode) {
    result = {
      ...result,
      selectedNodeModelPath:
        parentNodePath.concat([childNode.uuid]) as Model.Path,
    };
  }
  return result;
}

function DeleteNode(
  project: Project.t,
  path: Model.Path):
    Project.t
{
  const model = Project.model(project);
  console.assert(Model.hasNode(model, path));

  const newModel = Model.deleteTerminus(model, path);
  return {
    ...Project.pushModel(project, newModel),
    selectedNodeModelPath:
      Model.maximalValidSubpath(
        newModel,
        project.selectedNodeModelPath),
  };
}

function RenameNode(
  project: Project.t,
  path: Model.Path,
  name: string | undefined):
    Project.t
{
  const model = Project.model(project);
  const node = Model.node(model, path) as Node.t;
  console.assert(node != undefined);

  return Project.pushModel(
    project,
    Model.replaceTerminusWith(
      model,
      path,
      {...node, name}));
}

function ReplaceNodeContents(
  project: Project.t,
  path: Model.Path,
  newNode: Node.t):
    Project.t
{
  // This is getting janky. A lot of cross-assumptions.
  console.assert(Model.node(Project.model(project), path)?.uuid == newNode.uuid);

  return Project.pushModel(
    project,
    Model.replaceTerminusWith(
      Project.model(project),
      path,
      newNode));
}

function AddFields(
  project: Project.t,
  node: PatternNode.t,
  path: Model.Path,
  fields: [string, Entity.Type][]):
    Project.t
{
  const model = Project.model(project);
  console.assert(node == Model.node(model, path));
  console.assert(fields.every(
    (([field, _]) => !PatternNode.hasField(node, field))));
  const newFields = {...node.fields};
  fields.forEach(([field, type]) => newFields[field] = type);
  const newNode = {...node, fields: newFields};
  const newModel = Model.replaceTerminusWith(model, path, newNode);

  let schema = project.targets.schema;
  for (let [field, type] of fields) {
    schema = addFieldToTargetsSchema(schema, field, type);
  }

  return {
    ...Project.pushModel(project, newModel),
    targets: {
      ...project.targets,
      schema,
    },
  };
}

function RemoveField(
  project: Project.t,
  node: PatternNode.t,
  path: Model.Path,
  field: string):
    Project.t
{
  const newFields = {...node.fields};
  delete newFields[field];

  const newNode = {
    ...node,
    fields: newFields,
    rules: node.rules.filter(
      // This could be better, perhaps.
      rule => !Rule.hasField(rule, field)
    ),
  };

  return Project.pushModel(
    project,
    Model.replaceTerminusWith(
      Project.model(project),
      path,
      newNode));
}

function RenameField(
  project: Project.t,
  node: PatternNode.t,
  path: Model.Path,
  oldName: string,
  newName: string):
    Project.t
{
  // XXX This is broken. We are ignoring the effects of the rename on nodes
  // higher up in the extraction tree.

  const fixRule = (rule: Rule.t): Rule.t => {
    if (Rule.hasField(rule, oldName)) {
      if (rule.type == 'atom') {
        return {
          ...rule,
          fields: rule.fields.map(
            field => (
              field == oldName ? newName : field
            )
          ),
        };
      } else {
        return {
          ...rule,
          rules: rule.rules.map(fixRule),
        };
      }
    } else {
      return rule;
    }
  };

  const newFields = {...node.fields};
  newFields[newName] = newFields[oldName];
  delete newFields[oldName];

  const newNode = {
    ...node,
    fields: newFields,
    rules: node.rules.map(fixRule),
  };

  return Project.pushModel(
    project,
    Model.replaceTerminusWith(
      Project.model(project),
      path,
      newNode));
}

function setFieldTypeInNode(
  node: Node.t,
  field: string,
  type: Entity.Type):
    Node.t
{
  // Janky -- rules may need to be updated.
  
  if (node.type == 'pattern') {
    return {
      ...node,
      fields: {
        ...node.fields,
        [field]: type,
      },
    };
  } else {
    return {
      ...node,
      children: node.children.map(
        child => setFieldTypeInNode(child, field, type)
      ),
    };
  }
}

function SetFieldType(
  project: Project.t,
  field: string,
  newType: Entity.Type,
  isLabel: boolean):
    Project.t
{
  const oldModel = Project.model(project);
  const newModel =
    Node.fieldType(oldModel, field) == newType ? oldModel :
      setFieldTypeInNode(oldModel, field, newType);
  const newSchema = project.targets.schema.map(
    entry => (entry.field == field ? {
      field,
      type: newType,
      is_label: isLabel,
    } : entry)
  );
  return {
    ...(
      newModel == oldModel ? project :
        Project.pushModel(project, newModel)),
    targets: {
      ...project.targets,
      schema: newSchema,
    },
  };
}

function AddRule(
  project: Project.t,
  node: Node.t,
  path: Model.Path,
  rule: Rule.t):
    Project.t
{
  const model = Project.model(project);
  console.assert(node == Model.node(model, path));
  const newNode = {...node, rules: node.rules.concat([rule])};
  const newModel = Model.replaceTerminusWith(model, path, newNode);
  return Project.pushModel(project, newModel);
}

function RemoveRules(
  project: Project.t,
  node: Node.t,
  path: Model.Path,
  rules: Set<Rule.t>):
    Project.t
{
  const model = Project.model(project);
  console.assert(node == Model.node(model, path));
  const newNode = {...node, rules: node.rules.filter(rule => !rules.has(rule))};
  const newModel = Model.replaceTerminusWith(model, path, newNode);
  return Project.pushModel(project, newModel);
}

function RemoveRule(
  project: Project.t,
  node: Node.t,
  path: Model.Path,
  rule: Rule.t):
    Project.t
{
  return RemoveRules(
    project,
    node,
    path,
    new Set([rule]),
  );
}

function ReplaceRule(
  project: Project.t,
  node: Node.t,
  path: Model.Path,
  oldRule: Rule.t,
  newRule: Rule.t):
    Project.t
{
  const model = Project.model(project);
  console.assert(node == Model.node(model, path));
  console.assert(node.rules.includes(oldRule));
  const newRules = [...node.rules];
  newRules.splice(node.rules.indexOf(oldRule), 1, newRule);
  const newNode = {
    ...node,
    rules: newRules,
  };
  const newModel = Model.replaceTerminusWith(model, path, newNode);
  return Project.pushModel(project, newModel);
}

function ScheduleModelRun(
  project: Project.t,
  modelIndex: number,
  recordNames: string[],
  pin: boolean,
):
    Project.t
{
  const keep = false;

  const modelRun = ModelRun.build(
    modelIndex,
    recordNames.map(RecordRun.build),
    keep,
    pin,
  );

  function rest() {
    const result = [];
    let numExtraModelRuns = keep ? 0 : 1;
    for (let modelRun of project.modelRuns) {
      if (modelRun.keep) {
        result.push(modelRun);
      } else if (numExtraModelRuns < project.settings.numExtraModelRunsToKeep) {
        result.push(modelRun);
        numExtraModelRuns++;
      }
    }
    return result;
  }

  return {
    ...project,
    modelRuns: [modelRun, ...rest()],
  };
}

function CancelModelRun(
  project: Project.t,
  uuid: UUID):
    Project.t
{
  return {
    ...project,
    modelRuns: project.modelRuns.map(
      modelRun => {
        if (modelRun.uuid == uuid) {
          return {
            ...modelRun,
            recordRuns: modelRun.recordRuns.map(
              recordRun => {
                if (RecordRun.isPending(recordRun)) {
                  return {
                    type: 'CanceledRecordRun',
                    uuid: recordRun.uuid,
                    recordName: recordRun.recordName,
                  };
                } else {
                  return recordRun;
                }
              }
            ),
          };
        } else {
          return modelRun;
        }
      }
    ),
  };
}

function UpdateModelRun(
  project: Project.t,
  uuid: UUID,
  keep: boolean,
  pin: boolean):
    Project.t
{
  return {
    ...project,
    modelRuns: project.modelRuns.map(
      modelRun => {
        if (modelRun.uuid == uuid) {
          return {...modelRun, keep, pin};
        } else {
          return modelRun;
        }
      }
    ),
  };
}

function UpdateModelRecordRun(
  project: Project.t,
  modelIndex: number,
  recordRun: RecordRun.t):
    Project.t
{
  // Push results if we find the right doc run UUID.
  // Else just silently drop the new doc run state.
  const modelRuns = project.modelRuns.map(
    modelRun => {
      if (modelRun.modelIndex == modelIndex) {
        return {
          ...modelRun,
          recordRuns: modelRun.recordRuns.map(
            oldRecordRun => {
              if (oldRecordRun.uuid == recordRun.uuid &&
                  oldRecordRun.type != 'CanceledRecordRun')
              {
                return recordRun;
              } else {
                return oldRecordRun;
              }
            }
          ),
        };
      } else {
        return modelRun;
      }
    }
  );
  return {...project, modelRuns};
}

function ChangeSettings(
  project: Project.t,
  changes: Partial<Settings.t>):
    Project.t
{
  return {
    ...project,
    settings: {
      ...project.settings,
      ...changes,
    },
  };
}

function ToggleAnnotationMode(
  project: Project.t):
    Project.t
{
  return {
    ...project,
    settings: {
      ...project.settings,
      annotationMode: !project.settings.annotationMode,
    },
  };
}

function Hack_UpdateProject(
  project: Project.t,
  changes: Partial<Project.t>):
    Project.t
{
  return {
    ...project,
    ...changes,
  };
}

// Reducer function
// ================

export default function mainReducer(
  project: Project.t, action: Action): Project.t
{
  // console.info('Reducing project', project, action);
  switch (action.type) {
    case 'SetProject':
      return SetProject(project, action.project);
    case 'ImportTargets':
      return ImportTargets(project, action.targets);
    case 'AddFieldToTargetsSchema':
      return AddFieldToTargetsSchema(project, action.field);
    case 'DeleteFieldFromTargetsSchema':
      return DeleteFieldFromTargetsSchema(project, action.field);
    case 'Undo':
      return Undo(project);
    case 'Redo':
      return Redo(project);
    case 'SetSelectedRecordName':
      return SetSelectedRecordName(project, action.recordName);
    case 'SetSelectedNode':
      return SetSelectedNode(project, action.path);
    case 'SetSelectedRule':
      return SetSelectedRule(project, action.path, action.rule);
    case 'AddTargetsToDoc':
      return AddTargetsToDoc(project, action.recordName);
    case 'DeleteTargetsForDoc':
      return DeleteTargetsForDoc(project, action.recordName);
    case 'SetSelectedField':
      return SetSelectedField(project, action.field);
    case 'SetTargetValue':
      return SetTargetValue(project, action.recordName, action.field, action.value);
    case 'ClearModel':
      return ClearModel(project);
    case 'PlaceIntoMerge':
      return PlaceIntoMerge(project, action.path);
    case 'PlaceIntoPickBest':
      return PlaceIntoPickBest(project, action.path);
    case 'AddChildNode':
      return AddChildNode(project, action.parentNode, action.parentNodePath,
                          action.childNode, action.setChildToSelectedNode);
    case 'DeleteNode':
      return DeleteNode(project, action.path);
    case 'RenameNode':
      return RenameNode(project, action.path, action.name);
    case 'SetFieldType':
      return SetFieldType(project, action.field, action.newType, action.isLabel);
    case 'ReplaceNodeContents':
      return ReplaceNodeContents(project, action.path, action.newNode);
    case 'AddFields':
      return AddFields(project, action.node, action.path, action.fields);
    case 'RemoveField':
      return RemoveField(project, action.node, action.path, action.field);
    case 'RenameField':
      return RenameField(project, action.node, action.path, action.oldName, action.newName);
    case 'AddRule':
      return AddRule(project, action.node, action.path, action.rule);
    case 'RemoveRule':
      return RemoveRule(project, action.node, action.path, action.rule);
    case 'ReplaceRule':
      return ReplaceRule(project, action.node, action.path, action.oldRule, action.newRule);
    case 'ScheduleModelRun':
      return ScheduleModelRun(project, action.modelIndex, action.recordNames, action.pin);
    case 'CancelModelRun':
      return CancelModelRun(project, action.uuid);
    case 'UpdateModelRun':
      return UpdateModelRun(project, action.uuid, action.keep, action.pin);
    case 'UpdateModelRecordRun':
      return UpdateModelRecordRun(project, action.modelIndex, action.recordRun);
    case 'ChangeSettings':
      return ChangeSettings(project, action.changes);
    case 'ToggleAnnotationMode':
      return ToggleAnnotationMode(project);
    case 'Hack_UpdateProject':
      return Hack_UpdateProject(project, action.changes);
  }
}
