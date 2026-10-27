<!DOCTYPE html>
<html>
<head>
    <title>Coding Agent</title>
    <link rel="stylesheet" href="style.css" />
</head>

<body>

<?php

$filename = __DIR__ . "/messages.txt";
$statusfile = __DIR__ . "/status.txt";
$errorfile = __DIR__ . "/errors.txt";


function addMessage($filename, $type, $message) {
    $handle = fopen($filename, "a");

    if ($handle) {
        $message = str_replace("|", "/", $message);
        $message = str_replace(["\r", "\n"], " ", $message);

        fwrite($handle, $type . "|" . $message . "\n");
        fclose($handle);
    }
}

// create messages.txt if not exists
if (!file_exists($filename)) {
    $handle = fopen($filename, "w");
    if ($handle) {
        fwrite($handle, "AGENT|Hello! What would you like me to build?\n");
        fclose($handle);
    }
}
// create status.txt if not exists
if (!file_exists($statusfile)) {
    $handle = fopen($statusfile, "w");
    if ($handle) {
        fwrite($handle, "TITLE|New Project\n");
        fwrite($handle, "STAGE|Waiting for prompt\n");
        fwrite($handle, "PROGRESS|0\n");
        fclose($handle);
    }
}
// create errors.txt if not exists
if (!file_exists($errorfile)) {
    $handle = fopen($errorfile, "w");
    if ($handle) {
        fclose($handle);
    }
}

// read project status
$projectTitle = "New Project";
$currentStage = "Waiting for prompt";
$progress = 0;

$handle = fopen($statusfile, "r");

if ($handle) {
    while (($line = fgets($handle)) !== false) {
        $line = trim($line);

        if ($line != "") {
            $data = explode("|", $line, 2);

            if ($data[0] == "TITLE") {
                $projectTitle = $data[1];
            } elseif ($data[0] == "STAGE") {
                $currentStage = $data[1];
            } elseif ($data[0] == "PROGRESS") {
                $progress = $data[1];
            }
        }
    }

    fclose($handle);
}





// check if prompt submitted
if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_POST["prompt"])) {
    $prompt = trim($_POST["prompt"]);

    $maxIterations = isset($_POST["max_iterations"])
        ? (int) $_POST["max_iterations"]
        : 3;

    // validate the prompt
    if ($prompt == "") {
        // Ignore empty submissions without adding chat messages.
    } elseif (strlen($prompt) > 5000) {
        addMessage($filename, "AGENT", "Your prompt is too long. Please keep it under 5000 characters.");
    } elseif ($maxIterations < 1 || $maxIterations > 5) {
        addMessage($filename, "AGENT", "Invalid iteration setting. Please select a value between 1 and 5.");
    } else {
        // locate Python, the agent script and launcher
        $projectFolder = dirname(__DIR__, 2);
        $pythonExe = $projectFolder . "/.venv/Scripts/python.exe";
        $launcherFile = $projectFolder . "/src/launch_agent.py";
        $promptFile = __DIR__ . "/pending_prompt.txt";

        // check that required files exist
        if (!file_exists($pythonExe)) {
            addMessage($filename, "AGENT", "Could not start the coding agent: Python virtual environment was not found.");
        } elseif (!file_exists($launcherFile)) {
            addMessage($filename, "AGENT", "Could not start the coding agent: launch_agent.py was not found.");
        } else {
            // save the prompt for the launcher
            $saved = file_put_contents($promptFile, $prompt, LOCK_EX);

            if ($saved === false) {
                addMessage($filename, "AGENT", "Could not save the prompt for the coding agent. Check file permissions.");
            } else {
                // append the user prompt
                addMessage($filename, "USER", $prompt);
                addMessage($filename, "AGENT", "Task submitted. Starting the coding agent...");

                // SEND PROMPT TO MANAGER AGENT
                $command = 'start "" /B "' . $pythonExe . '" "' . $launcherFile . '" ' . $maxIterations;

                exec($command, $output, $returnCode);

                if ($returnCode !== 0) {
                    addMessage($filename, "AGENT", "Could not launch the Python launcher. Check the Errors panel.");

                    $handle = fopen($errorfile, "a");

                    if ($handle) {
                        fwrite($handle, "Python launcher command failed. Exit code: " . $returnCode . "\n");
                        fclose($handle);
                    }
                }
            }
        }
    }
}





?>

<div class="container">

    <div class="left">

        <div class="header">
            Coding Agent
        </div>
        <div class="project-status">

            <div class="reset-button">
                <form action="reset.php" method="POST"
                    onsubmit="return confirm('Reset everything? This will delete all generated workspace files and clear the chat, logs and errors.');">
                    <button type="submit">Reset</button>
                </form>
            </div>

            <div class="project-title" id="projectTitle">
                <?php echo htmlspecialchars($projectTitle, ENT_QUOTES, "UTF-8"); ?>
            </div>

            <div class="project-stage" id="projectStage">
                Stage:
                <strong id="stageText">
                    <?php echo htmlspecialchars($currentStage, ENT_QUOTES, "UTF-8"); ?>
                </strong>
            </div>

            <div class="progress-container">

                <div
                    class="progress-bar" id="progressBar" 
                    style="width: <?php echo $progress; ?>%;"
                >
                </div>

            </div>

            <div class="progress-text" id="progressText">
                <?php echo $progress; ?>%
            </div>

        </div>
        <div class="messages" id="messages">
            <?php
            $handle = fopen($filename, "r");
            if ($handle) {
                // print all messages
                while (($line = fgets($handle)) !== false) {
                    $line = trim($line);
                    if ($line != "") {
                        $data = explode("|", $line, 2);

                        $type = $data[0];
                        $message = $data[1];

                        if ($type == "USER") {
                            echo "<div class=\"message user\">";
                            echo "<strong>You:</strong><br>";
                        } else {
                            echo "<div class=\"message\">";
                            echo "<strong>Agent:</strong><br>";
                        }
                        echo htmlspecialchars($message, ENT_QUOTES, "UTF-8");
                        echo "</div>";
                    }
                }
                fclose($handle);
            }
            ?>

        </div>

        <form class="input-area" method="post" action="index.php">

            <textarea name="prompt"
                placeholder="Tell the coding agent what to build..."></textarea>

            <div class="iteration-setting">
                <label for="max_iterations">Max <br> Iterations:</label>
                <select name="max_iterations" id="max_iterations">
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3" selected>3</option>
                    <option value="4">4</option>
                    <option value="5">5</option>
                </select>
            </div>

            <button type="submit">Send</button>

        </form>

    </div>


    <div class="right">

        <div class="header">
            Sandbox
        </div>

        <div class="sandbox">
            <iframe src="sandbox.html" style="width: 100%; height: 650px;"></iframe>
        </div>

        <div class="errors">
            <div class="errors-title">
                Errors
            </div>
            <div class="error-list" id="errorList">
                <?php
                $handle = fopen($errorfile, "r");
                if ($handle) {

                    $hasErrors = false;

                    while (($line = fgets($handle)) !== false) {

                        $line = trim($line);

                        if ($line != "") {

                            $hasErrors = true;

                            echo "<div class=\"error\">";
                            echo htmlspecialchars(
                                $line,
                                ENT_QUOTES,
                                "UTF-8"
                            );
                            echo "</div>";
                        }
                    }
                    fclose($handle);
                    if (!$hasErrors) {
                        echo "<div class=\"no-errors\">";
                        echo "No errors reported.";
                        echo "</div>";
                    }
                }
                ?>
            </div>
        </div>

    </div>

</div>

<script>

let previousMessages = [];
let previousErrors = "";
let previousStatus = "";

async function refreshAgentUI() {
    try {
        const response = await fetch("get_status.php", {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error("Could not load agent status");
        }

        const data = await response.json();

        // Update project status only when it changes
        const currentStatus = JSON.stringify(data.status);

        if (currentStatus !== previousStatus) {
            document.getElementById("projectTitle").textContent =
                data.status.title;

            document.getElementById("stageText").textContent =
                data.status.stage;

            document.getElementById("progressBar").style.width =
                data.status.progress + "%";

            document.getElementById("progressText").textContent =
                data.status.progress + "%";

            previousStatus = currentStatus;
        }


        // Update chat messages only when they change
        const messages = document.getElementById("messages");

        const currentMessages = data.messages;
        const currentMessagesJSON = JSON.stringify(currentMessages);

        if (currentMessagesJSON !== JSON.stringify(previousMessages)) {
            const wasAtBottom =
                messages.scrollHeight - messages.scrollTop -
                messages.clientHeight < 40;

            messages.replaceChildren();

            currentMessages.forEach(function(item) {
                const messageDiv = document.createElement("div");

                messageDiv.className = item.type === "USER"
                    ? "message user"
                    : "message";

                const heading = document.createElement("strong");
                heading.textContent = item.type === "USER"
                    ? "You:"
                    : "Agent:";

                messageDiv.appendChild(heading);
                messageDiv.appendChild(document.createElement("br"));

                messageDiv.appendChild(
                    document.createTextNode(item.message)
                );

                messages.appendChild(messageDiv);
            });

            previousMessages = currentMessages.map(item => ({
                type: item.type,
                message: item.message
            }));

            if (wasAtBottom) {
                messages.scrollTop = messages.scrollHeight;
            }
        }


        // Update errors only when their contents change
        const currentErrors = JSON.stringify(data.errors);

        if (currentErrors !== previousErrors) {
            const errorList = document.getElementById("errorList");
            errorList.replaceChildren();

            if (data.errors.length === 0 ||
                data.errors.every(line => line.trim() === "")) {

                const noErrors = document.createElement("div");
                noErrors.className = "no-errors";
                noErrors.textContent = "No errors reported.";

                errorList.appendChild(noErrors);

            } else {
                data.errors.forEach(function(line) {
                    if (line.trim() === "") {
                        return;
                    }

                    const errorDiv = document.createElement("div");
                    errorDiv.className = "error";
                    errorDiv.textContent = line;

                    errorList.appendChild(errorDiv);
                });
            }

            previousErrors = currentErrors;
        }

    } catch (error) {
        console.error("UI refresh failed:", error);
    }
}

// Load current data immediately
refreshAgentUI();

// Check for updates every 1.5 seconds
setInterval(refreshAgentUI, 1500);
</script>


</body>
</html>
