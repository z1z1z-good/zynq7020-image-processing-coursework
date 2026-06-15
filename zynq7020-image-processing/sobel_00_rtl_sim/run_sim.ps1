param(
    [int]$Width = 128,
    [int]$Height = 72,
    [int]$ClkFreq = 12000000,
    [int]$BaudRate = 1000000,
    [string]$Python = "python",
    [string]$Iverilog = "iverilog",
    [string]$Vvp = "vvp",
    [ValidateSet("auto", "icarus", "modelsim", "xsim")]
    [string]$Simulator = "auto",
    [string]$ModelSimBin = "D:\FPGA\ModelSim\win64",
    [string]$XSimBin = "D:\Vivado\Vivado\2023.2\bin",
    [switch]$UseWsl
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

function Test-Tool {
    param([string]$Name)

    return [bool](Resolve-Tool $Name @())
}

function Resolve-Tool {
    param(
        [string]$Name,
        [string[]]$Candidates
    )

    if (Test-Path -LiteralPath $Name -PathType Leaf) {
        return (Resolve-Path -LiteralPath $Name).Path
    }

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    foreach ($candidate in $Candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    return $null
}

function Invoke-Checked {
    param(
        [string]$Command,
        [object[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE`: $Command"
    }
}

function Convert-To-WslPath {
    param([string]$Path)

    $fullPath = (Resolve-Path -LiteralPath $Path).Path
    $drive = $fullPath.Substring(0, 1).ToLowerInvariant()
    $rest = $fullPath.Substring(2).Replace("\", "/")
    return "/mnt/$drive$rest"
}

if ($UseWsl) {
    if (-not (Test-Tool "wsl")) {
        throw "WSL was requested but 'wsl.exe' was not found."
    }

    $wslDir = Convert-To-WslPath $ScriptDir
    $cmd = "cd '$wslDir' && make sim WIDTH=$Width HEIGHT=$Height CLK_FREQ=$ClkFreq BAUD_RATE=$BaudRate"
    wsl -- bash -lc $cmd
    exit $LASTEXITCODE
}

$PythonCommand = Resolve-Tool $Python @()
if (-not $PythonCommand) {
    throw "Required Python command '$Python' was not found."
}

$BuildDir = "build"
$Top = "sobel_system_tb"
$VvpOut = Join-Path $BuildDir "$Top.vvp"
$VcdOut = Join-Path $BuildDir "$Top.vcd"

if (($Width -eq 128) -and ($Height -eq 72)) {
    $InputHex = "data/input_rgb.hex"
} else {
    $InputHex = Join-Path $BuildDir "input_rgb.hex"
}

$PgmOut = Join-Path $BuildDir "sobel_out.pgm"
$InputPng = Join-Path $BuildDir "input_rgb.png"
$SobelPng = Join-Path $BuildDir "sobel_out.png"

New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null

Invoke-Checked $PythonCommand @(
    "tools/gen_input_rgb.py",
    "--width", $Width,
    "--height", $Height,
    "--output", $InputHex
)

$rtl = @(
    "rtl/uart_rx.v",
    "rtl/image_frame_rx.v",
    "rtl/rgb_to_gray.v",
    "rtl/sobel_core.v",
    "rtl/video_stream_model.v",
    "rtl/sobel_system.v"
)

$defines = @(
    "-DIMG_WIDTH=$Width",
    "-DIMG_HEIGHT=$Height",
    "-DCLK_FREQ=$ClkFreq",
    "-DBAUD_RATE=$BaudRate",
    "-DINPUT_RGB_HEX=`"$InputHex`"",
    "-DOUTPUT_PGM=`"$PgmOut`"",
    "-DVCD_FILE=`"$VcdOut`""
)

$IverilogCommand = Resolve-Tool $Iverilog @()
$VvpCommand = Resolve-Tool $Vvp @()
$VlibCommand = Resolve-Tool "vlib" @((Join-Path $ModelSimBin "vlib.exe"))
$VlogCommand = Resolve-Tool "vlog" @((Join-Path $ModelSimBin "vlog.exe"))
$VsimCommand = Resolve-Tool "vsim" @((Join-Path $ModelSimBin "vsim.exe"))
$XvlogCommand = Resolve-Tool "xvlog" @(
    (Join-Path $XSimBin "xvlog.bat")
)
$XelabCommand = Resolve-Tool "xelab" @(
    (Join-Path $XSimBin "xelab.bat")
)
$XsimCommand = Resolve-Tool "xsim" @(
    (Join-Path $XSimBin "xsim.bat")
)

if ($Simulator -eq "auto") {
    if ($IverilogCommand -and $VvpCommand) {
        $Simulator = "icarus"
    } elseif ($VlibCommand -and $VlogCommand -and $VsimCommand) {
        $Simulator = "modelsim"
    } elseif ($XvlogCommand -and $XelabCommand -and $XsimCommand) {
        $Simulator = "xsim"
    } else {
        throw "No supported simulator was found. Install Icarus, ModelSim, or XSim, or use -UseWsl."
    }
}

Write-Host "Selected simulator: $Simulator"

switch ($Simulator) {
    "icarus" {
        if (-not $IverilogCommand -or -not $VvpCommand) {
            throw "Icarus was selected but iverilog or vvp was not found."
        }

        Invoke-Checked $IverilogCommand (@("-g2005-sv") + $defines + @("-o", $VvpOut, "tb/sobel_system_tb.v") + $rtl)
        Invoke-Checked $VvpCommand @($VvpOut)
    }

    "modelsim" {
        if (-not $VlibCommand -or -not $VlogCommand -or -not $VsimCommand) {
            throw "ModelSim was selected but vlib, vlog, or vsim was not found."
        }

        $ModelSimWork = Join-Path $BuildDir "modelsim_work"
        if (-not (Test-Path -LiteralPath (Join-Path $ModelSimWork "_info"))) {
            Invoke-Checked $VlibCommand @($ModelSimWork)
        }

        Invoke-Checked $VlogCommand (@("-sv", "-work", $ModelSimWork, "tb/sobel_system_tb.v") + $rtl)
        $ModelSimWorkArg = $ModelSimWork.Replace("\", "/")
        Invoke-Checked $VsimCommand @(
            "-c",
            "-lib", $ModelSimWorkArg,
            $Top,
            "-do", "run -all; quit -f"
        )
    }

    "xsim" {
        if (-not $XvlogCommand -or -not $XelabCommand -or -not $XsimCommand) {
            throw "XSim was selected but xvlog, xelab, or xsim was not found."
        }

        $SourceRoot = $ScriptDir.Replace("\", "/")
        $XSimOptions = @(
            "--sv",
            "--define=IMG_WIDTH=$Width",
            "--define=IMG_HEIGHT=$Height",
            "--define=CLK_FREQ=$ClkFreq",
            "--define=BAUD_RATE=$BaudRate"
        )
        $XSimSources = @("$SourceRoot/tb/sobel_system_tb.v") +
            ($rtl | ForEach-Object { "$SourceRoot/$($_.Replace('\', '/'))" })
        $XSimOptionsFile = Join-Path $BuildDir "xvlog_options.f"
        [System.IO.File]::WriteAllLines(
            $XSimOptionsFile,
            $XSimOptions + ($XSimSources | ForEach-Object { "`"$_`"" }),
            [System.Text.Encoding]::ASCII
        )
        New-Item -ItemType Directory -Force -Path (Join-Path $BuildDir "data") | Out-Null
        New-Item -ItemType Directory -Force -Path (Join-Path $BuildDir "build") | Out-Null
        Copy-Item -LiteralPath $InputHex -Destination (Join-Path $BuildDir "data\input_rgb.hex") -Force

        Push-Location $BuildDir
        try {
            Invoke-Checked $XvlogCommand @("-f", "xvlog_options.f")
            Invoke-Checked $XelabCommand @("--debug", "typical", "--snapshot", "${Top}_sim", $Top)
            Invoke-Checked $XsimCommand @("${Top}_sim", "--runall")
        } finally {
            Pop-Location
        }
        Copy-Item -LiteralPath (Join-Path $BuildDir "build\sobel_out.pgm") -Destination $PgmOut -Force
        Copy-Item -LiteralPath (Join-Path $BuildDir "build\sobel_system_tb.vcd") -Destination $VcdOut -Force
    }
}

Invoke-Checked $PythonCommand @(
    "tools/convert_images.py",
    "--width", $Width,
    "--height", $Height,
    "--input-rgb", $InputHex,
    "--sobel-pgm", $PgmOut,
    "--input-png", $InputPng,
    "--sobel-png", $SobelPng
)

Write-Host "Simulation finished."
Write-Host "Simulator: $Simulator"
Write-Host "Output image: $SobelPng"
Write-Host "Waveform: $VcdOut"
