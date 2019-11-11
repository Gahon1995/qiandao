function get_init_code() {
    let version = "# version: Python3\n\n";
    let codeAreaTip = "# please edit your code here:\n";
    let codeStart = "# code start\n\n";
    let codeEnd = "# code end\n\n";
    let codeTip = " '''\nThis function is the entry of this program and\nit must be return your answer of current question.\n'''\n";
    let code = "# Python 3 Types (otherwise Identifiers)\n" +
        "bytearray bytes filter map memoryview open range zip\n" +
        "# Some Example code\n" +
        "import os\n" +
        "from package import ParentClass\n" +
        "@nonsenseDecorator\n" +
        "def doesNothing():\n" +
        "    pass\n" +
        "class ExampleClass(ParentClass):\n" +
        "    @staticmethod\n" +
        "    def example(inputStr):\n" +
        "        a = list(inputStr)\n" +
        "        a.reverse()\n" +
        "        return ''.join(a)\n" +
        "    def __init__(self, mixin = 'Hello'):\n" +
        "        self.mixin = mixin\n" +
        "          ";
    return version + codeAreaTip + codeStart + codeEnd + codeTip + code
}

function cmOption() {
    return {
        // autoCloseBrackets: true,
        tabSize: 4,
        // styleActiveLine: true,
        lineNumbers: true,
        line: true,
        mode: 'text/x-python',
        theme: 'base16-light',
        keyMap: "emacs",
        smartIndent: true, //智能缩进
        indentUnit: 2, // 智能缩进单位为4个空格长度
        indentWithTabs: true,  // 使用制表符进行智能缩进
        lineWrapping: true,//
        // 在行槽中添加行号显示器、折叠器、语法检测器`
        gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter", "CodeMirror-lint-markers"],
        foldGutter: true, // 启用行槽中的代码折叠
        autofocus: true,  //自动聚焦
        matchBrackets: true,// 匹配结束符号，比如"]、}"
        autoCloseBrackets: true, // 自动闭合符号
        styleActiveLine: true, // 显示选中行的样式
        height: 600
    }
}


const app = new Vue({
    el: '#app',
    data: function () {
        return {
            loading: true,
            editor: null,
            submit: false,
            form: {
                har: get_init_code(),
                variables: {},
                setting: {
                    sitename: "测试网址",
                    siteurl: "www.test.com",
                    note: "",
                    type: "1",
                    cron: "0 0 0 01",
                    interval: "86400"
                }
            },
            cmOption: cmOption()
        }
    },
    methods: {
        handleSubmit() {
            this.loading = true;
            console.log(this.form)
        }

    }
});

// app.handleSubmit = function handleSubmit() {
//     console.log("save")
// };
