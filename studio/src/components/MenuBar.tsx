import React from 'react';

import * as Targets from 'studio/foundation/targets';
import * as RecordTargets from 'studio/foundation/recordTargets';

import {Value as TheModalContext} from 'studio/context/ModalContext';
import {Value as TheSessionContext} from 'studio/context/SessionContext';
import {Value as TheActionContext} from 'studio/context/ActionContext';

import AutosaverText from 'studio/components/AutosaverText';
import ModelRunsDialog from 'studio/components/ModelRunsDialog';
import BlueprintSettingsDialog from 'studio/components/BlueprintSettingsDialog';
import StudioSettingsDialog from 'studio/components/StudioSettingsDialog';
import Menu, {Props as MenuProps} from 'studio/components/Menu';

import {rawLoadResponse, loadRecordNames} from 'studio/async/loadRecords';
import loadDoc from 'studio/async/loadDoc';

import * as Project from 'studio/state/project';
import * as Settings from 'studio/state/settings';

import useKeyboardShortcut from 'studio/hooks/useKeyboardShortcut';
import {clear as clearRecentProjects} from 'studio/hooks/useRecentProjectsList';

import makeDebugBundle from 'studio/util/makeDebugBundle';

import './MenuBar.css';

type Props = {
  project: Project.t | undefined,
  haveModal: boolean,
  modalContext: TheModalContext,
  sessionContext: TheSessionContext,
  actionContext: TheActionContext,
};

export default function MenuBar({
  project,
  haveModal,
  modalContext,
  sessionContext,
  actionContext,
}: Props) {

  const [openMenuName, setOpenMenuName] =
    React.useState<string | undefined>(undefined);

  const buttonClicked = (menuName: MenuName) => {
    if (menuName == openMenuName) {
      setOpenMenuName(undefined);
    } else {
      setOpenMenuName(menuName);
    }
  };

  const closeAllMenus = () => {
    setOpenMenuName(undefined);
  };

  // File
  // ====

  // Edit
  // ====

  const canUndo = project != undefined &&
                  Project.canUndo(project);
  const undoCB = React.useCallback(() => {
    if (canUndo) {
      actionContext.dispatchAction({type: 'Undo'});
    }
  }, [actionContext, canUndo]);
  useKeyboardShortcut({key: 'z', metaKey: true}, undoCB);

  const canRedo = project != undefined &&
                  Project.canRedo(project);
  const redoCB = React.useCallback(() => {
    if (canRedo) {
      actionContext.dispatchAction({type: 'Redo'});
    }
  }, [actionContext, canRedo]);
  useKeyboardShortcut({key: 'z', metaKey: true, shiftKey: true}, redoCB);

  const blueprintSettingsCB = React.useCallback(() => {
    modalContext.dispatchModalAction({
      name: 'ShowModal',
      modal: <BlueprintSettingsDialog project={project as Project.t} />,
    });
  }, [modalContext, project]);

  const studioSettingsCB = React.useCallback(() => {
    modalContext.dispatchModalAction({
      name: 'ShowModal',
      modal: <StudioSettingsDialog/>,
    });
  }, [modalContext]);

  // Docs
  // ====

  const filterDocsByTagCB = React.useCallback(
    () => {
      if (project) {
        const result = prompt(
          'What tags would you like to filter docs by? ' +
          'Every listed tag will be required.\n\n' +
          '(Example: "adp high_quality")\n\n' +
          `Available tags: ${Targets.tagsPresentInSomeDoc(project.targets).concat().sort().join(', ')}`,
          project.settings.requiredDocTags,
        );

        if (result != null) {
          actionContext.dispatchAction({
            type: 'ChangeSettings',
            changes: {requiredDocTags: result},
          });
        }
      }
    },
    [
      project?.targets,
      project?.settings.requiredDocTags,
      actionContext,
    ],
  );

  // Model
  // =====

  const viewModelRunsCB = React.useCallback(() => {
    if (project) {
      modalContext.dispatchModalAction({
        name: 'ShowModal',
        modal: <ModelRunsDialog/>,
      });
    }
  }, [modalContext, project]);

  // Targets
  // =======

  /*
  const deleteTargetsForThisDocCB = React.useCallback(() => {
    const recordName = project?.selectedRecordName;

    if (recordName != undefined) {
      actionContext.dispatchAction({type: 'DeleteTargetsForDoc', recordName});
    }
  }, [actionContext, project?.selectedRecordName]);
  */

  // Results
  // =======

  const chooseFLAFieldsCB = React.useCallback(
    () => {
      const result = prompt(
        'What fields would you like to be included in FLA/STP calculations?\n\n' +
        '(Example: "net_pay total_taxes pay_date")',
        project?.settings.flaFields,
      );

      if (result != null) {
        actionContext.dispatchAction({
          type: 'ChangeSettings',
          changes: {flaFields: result},
        });
      }
    },
    [
      project?.settings.flaFields,
      actionContext,
    ],
  );

  const scrubTargetsCB = React.useCallback(
    () => {
      if (project?.targets) {
        const confirmed = confirm(
          'This will change every empty string or null target value ' +
          'in your targets to an unknown target value.\n\n' +
          'Normally, if a target value is textual and has an empty string, ' +
          'we expect some entity to be extracted which has no text, ' +
          'and if a target value for some field is null, ' +
          'we expect NO entity to be extracted for the corresponding field, ' +
          'otherwise FLA/STP is negatively impacted.\n\n' +
          'Running this operation will change every empty-string/null target value ' +
          'to an "unknown" target value, which means that field is not used ' +
          'for FLA/STP calculation.\n\n' +
          'This operation cannot be undone.'
        );

        if (confirmed) {
          const reallyConfirmed = confirm(
            'Are you really, really sure? This cannot be undone.'
          );

          if (reallyConfirmed) {
            const oldTargets = project.targets;
            const newTargets = {
              ...oldTargets,
              doc_targets: oldTargets.doc_targets.map(
                recordTargets => ({
                  ...recordTargets,
                  assignments: recordTargets.assignments.filter(
                    ({field, value}) => (
                      value.text
                    )
                  ),
                })
              ),
            };

            actionContext.dispatchAction({
              type: 'Hack_UpdateProject',
              changes: {
                targets: newTargets,
              },
            });
          }
        }
      }
    },
    [
      project?.targets,
      actionContext,
    ],
  );

  // Menu
  // ====

  return (
    <div className="MenuBar">
      <MenuBarButton
        text="File"
        open={openMenuName == 'File'}
        onClick={() => buttonClicked('File')}
        menu={{
          rows: [
            {
              text: 'Close project',
              type: 'ActionRow',
              action: (
                () => sessionContext.setProjectPath(undefined)
              ),
              disabled: !project,
            },
          ],
          onActionExecute: closeAllMenus,
        }}
      />

      <MenuBarButton
        text="Edit"
        open={openMenuName == 'Edit'}
        onClick={() => buttonClicked('Edit')}
        menu={{
          rows: [
            {
              text: 'Undo',
              type: 'ActionRow',
              action: (
                undoCB
              ),
              disabled: !canUndo,
            },
            {
              text: 'Redo',
              type: 'ActionRow',
              action: (
                redoCB
              ),
              disabled: !canRedo,
            },
            {
              text: 'Blueprint settings...',
              type: 'ActionRow',
              action: (
                blueprintSettingsCB
              ),
              disabled: !project,
            },
            {
              text: 'Studio settings...',
              type: 'ActionRow',
              action: (
                studioSettingsCB
              ),
            },
          ],
          onActionExecute: closeAllMenus,
        }}
      />

      <MenuBarButton
        text="View"
        open={openMenuName == 'View'}
        onClick={() => buttonClicked('View')}
        menu={{
          rows: [
            {
              text: 'Toggle annotation mode',
              type: 'ActionRow',
              action: (
                () => {
                  actionContext.dispatchAction({
                    type: 'ToggleAnnotationMode',
                  });
                }
              ),
              disabled: !project,
            },
          ],
          onActionExecute: closeAllMenus,
        }}
      />

      <MenuBarButton
        text="Docs"
        open={openMenuName == 'Docs'}
        onClick={() => buttonClicked('Docs')}
        menu={{
          rows: [
            {
              text: 'Filter docs by tag...',
              type: 'ActionRow',
              action: (
                filterDocsByTagCB
              ),
              disabled: !project,
            },
            {
              text: 'Download doc',
              type: 'ActionRow',
              action: (
                () => {
                  if (project && project.selectedRecordName) {
                    loadDoc(
                      project.samplesPath,
                      project.selectedRecordName,
                      Project.blueprintSettings(project),
                      sessionContext,
                    ).then(
                      doc => {
                        saveData(
                          JSON.stringify(doc),
                          'doc.json',
                        );
                      }
                    );
                  }
                }
              ),
              disabled: !project?.selectedRecordName,
            },
          ],
          onActionExecute: closeAllMenus,
        }}
      />

      <MenuBarButton
        text="Model"
        open={openMenuName == 'Model'}
        onClick={() => buttonClicked('Model')}
        menu={{
          rows: [
            {
              text: 'Download model JSON',
              type: 'ActionRow',
              action: (
                () => {
                  if (project) {
                    saveData(
                      JSON.stringify(Project.model(project)),
                      'model.json',
                    );
                  }
                }
              ),
              disabled: !project,
            },
            {
              text: 'Clear model',
              type: 'ActionRow',
              action: (
                () => actionContext.dispatchAction({type: 'ClearModel'})
              ),
              disabled: !project,
            },
          ],
          onActionExecute: closeAllMenus,
        }}
      />

      <MenuBarButton
        text="Results"
        open={openMenuName == 'Results'}
        onClick={() => buttonClicked('Results')}
        menu={{
          rows: [
            {
              text: 'View model runs...',
              type: 'ActionRow',
              action: (
                viewModelRunsCB
              ),
              disabled: !project,
            },
            {
              text: 'Choose FLA/STP fields...',
              type: 'ActionRow',
              action: (
                chooseFLAFieldsCB
              ),
              disabled: !project,
            },
          ],
          onActionExecute: closeAllMenus,
        }}
      />

      <MenuBarButton
        text="Targets"
        open={openMenuName == 'Targets'}
        onClick={() => buttonClicked('Targets')}
        menu={{
          rows: [
            {
              text: 'Scrub targets...',
              type: 'ActionRow',
              action: (
                scrubTargetsCB
              ),
              disabled: !project,
            },
            {
              text: 'Download targets',
              type: 'ActionRow',
              action: (
                () => {
                  if (project) {
                    saveData(
                      JSON.stringify(project?.targets),
                      'targets.json',
                    );
                  }
                }
              ),
              disabled: !project,
            },
          ],
          onActionExecute: closeAllMenus,
        }}
      />

      <MenuBarButton
        text="Debug"
        open={openMenuName == 'Debug'}
        onClick={() => buttonClicked('Debug')}
        menu={{
          rows: [
            {
              text: 'Reset layout',
              type: 'ActionRow',
              action: (
                () => {
                  const keys = [...Object.keys(window.localStorage)].filter(
                    key => (
                      key.startsWith('Studio.TableView') ||
                      key.startsWith('Studio.Split')
                    )
                  );

                  keys.forEach(key => localStorage.removeItem(key));
                  window.location.reload();
                }
              ),
            },
            {
              text: 'Reset entire GUI',
              type: 'ActionRow',
              action: (
                () => {
                  localStorage.clear();
                  window.location.reload();
                }
              ),
            },
            {
              text: 'Download load_records response',
              disabled: !project,
              type: 'ActionRow',
              action: (
                () => {
                  if (project) {
                    rawLoadResponse(project.samplesPath).then(
                      response => {
                        saveData(
                          JSON.stringify(response),
                          'load_records_response.json',
                        );
                      }
                    );
                  }
                }
              ),
            },
            {
              text: 'Download debug data',
              disabled: !project,
              type: 'ActionRow',
              action: (
                () => {
                  if (project) {
                    makeDebugBundle(
                      project,
                      sessionContext,
                    );
                  }
                }
              ),
            },
          ],
          onActionExecute: closeAllMenus,
        }}
      />

      <MenuBarButton
        text="Help"
        open={openMenuName == 'Help'}
        onClick={() => buttonClicked('Help')}
        menu={{
          rows: [
            {
              text: 'Mouse/keyboard shortcuts...',
              type: 'ActionRow',
              action: (
                () => {
                  alert(`

Document view:

Wheel: zoom in/out
Cmd+Wheel: pan

Keyboard shortcuts:

d: Select next doc
Shift+d: Select previous doc
f: Select next field
Shift+f: Select previous field
c: Clear field/rule selection

                  `);
                }
              ),
            },
          ],
          onActionExecute: closeAllMenus,
        }}
      />
    </div>
  )
}

function saveData(blob: string, filename: string) {
  const a = document.createElement('a');
  a.style.display = 'none';
  a.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(blob));
  a.download = filename;
  document.body.appendChild(a);
  a.click();
}

type MenuBarButtonProps = {
  text: string;
  open: boolean;
  menu: MenuProps;
  onClick: () => void;
};

function MenuBarButton(props: MenuBarButtonProps) {
  return (
    <div
      className={
        '_button SmallText' +
        (props.open ? ' _open' : '')}
      onClick={
        event => {
          event.stopPropagation();
          event.preventDefault();
          props.onClick();
        }
      }
    >
      {props.text}
      {props.open && <Menu
        rows={props.menu.rows}
        onActionExecute={props.menu.onActionExecute}
      />}
    </div>
  );
}

type MenuName =
  | 'Debug'
  | 'Docs'
  | 'View'
  | 'Edit'
  | 'File'
  | 'Help'
  | 'Model'
  | 'Results'
  | 'Targets'
;
