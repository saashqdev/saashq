saashq.ui.form.ControlJSON = class ControlCode extends saashq.ui.form.ControlCode {
	set_language() {
		this.editor.session.setMode("ace/mode/json");
		this.editor.setKeyboardHandler("ace/keyboard/vscode");
	}
};
