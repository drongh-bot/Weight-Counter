const vscode = require('vscode');
const path = require('path');
const cp = require('child_process');
const iconv = require('iconv-lite');

// Get executable inside .venv (uv-compatible)
function getVenvExe(exeName) {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders) {
        vscode.window.showErrorMessage("Please open a workspace first.");
        return null;
    }

    const root = folders[0].uri.fsPath;
    const isWin = process.platform === 'win32';
    const exe = exeName + (isWin ? '.exe' : '');

    return path.join(root, '.venv', isWin ? 'Scripts' : 'bin', exe);
}

// Safe command runner
function runCommand(exe, args, onSuccess, onError) {
    if (!exe) return;

    const child = cp.spawn(exe, args, { encoding: 'buffer' });

    let stderrData = Buffer.alloc(0);

    child.stderr.on('data', data => {
        stderrData = Buffer.concat([stderrData, data]);
    });

    child.on('close', code => {
        if (code === 0) {
            onSuccess();
        } else {
            const msg = iconv.decode(stderrData, 'utf8');
            onError(msg);
        }
    });
}

function activate(context) {

    // -------------------------
    // 1. Compile UI
    // -------------------------
    const compileUI = vscode.commands.registerCommand('pyside.compileUI', (uri) => {
        if (!uri) {
            vscode.window.showErrorMessage("Please right-click a .ui file to run this command.");
            return;
        }

        const input = uri.fsPath;
        const dir = path.dirname(input);
        const base = path.basename(input, '.ui');
        const output = path.join(dir, `ui_${base}.py`);

        const exe = getVenvExe('pyside6-uic');

        runCommand(
            exe,
            [input, '-o', output],
            () => vscode.window.showInformationMessage(`UI compiled → ${output}`),
            (err) => vscode.window.showErrorMessage(`UI compile failed: ${err}`)
        );
    });


    // -------------------------
    // 2. Compile RCC
    // -------------------------
    const compileRCC = vscode.commands.registerCommand('pyside.compileRCC', (uri) => {
        if (!uri) {
            vscode.window.showErrorMessage("Please right-click a .qrc file to run this command.");
            return;
        }

        const input = uri.fsPath;
        const dir = path.dirname(input);
        const base = path.basename(input, '.qrc');
        const output = path.join(dir, `${base}_rc.py`);

        const exe = getVenvExe('pyside6-rcc');

        runCommand(
            exe,
            [input, '-o', output],
            () => vscode.window.showInformationMessage(`RCC compiled → ${output}`),
            (err) => vscode.window.showErrorMessage(`RCC compile failed: ${err}`)
        );
    });


    // -------------------------
    // 3. Open UI in Designer
    // -------------------------
    const openUI = vscode.commands.registerCommand('pyside.openUI', (uri) => {
        if (!uri) {
            vscode.window.showErrorMessage("Please right-click a .ui file to run this command.");
            return;
        }

        const exe = getVenvExe('pyside6-designer');
        if (!exe) return;

        cp.exec(`"${exe}" "${uri.fsPath}"`, (err) => {
            if (err) {
                vscode.window.showErrorMessage("Failed to launch Qt Designer. Please ensure PySide6 is installed in .venv.");
            }
        });
    });


    // -------------------------
    // 4. Open Designer (New UI)
    // -------------------------
    const createUI = vscode.commands.registerCommand('pyside.createUI', (uri) => {
        if (!uri) {
            vscode.window.showErrorMessage("Please right-click a folder to run this command.");
            return;
        }

        const exe = getVenvExe('pyside6-designer');
        if (!exe) return;

        cp.exec(`"${exe}"`, (err) => {
            if (err) {
                vscode.window.showErrorMessage("Failed to launch Qt Designer. Please ensure PySide6 is installed in .venv.");
            }
        });
    });

    context.subscriptions.push(compileUI, compileRCC, openUI, createUI);
}

function deactivate() {}

module.exports = { activate, deactivate };
