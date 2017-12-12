from cx_Freeze import setup, Executable

setup(
    name = "CA_Control",
    version = "0.1",
    description = "CA Control by XOMRKOB",
    executables = [Executable("main.pyw")]
)
