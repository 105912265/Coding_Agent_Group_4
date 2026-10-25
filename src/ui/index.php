<!DOCTYPE html>
<html>
<head>
    <title>Coding Agent</title>
    <link rel="stylesheet" href="style.css" />
</head>

<body>

<?php
// create data directory
umask(0007);
$dir = "../../data/cos30018";
if (!is_dir($dir)) {
    mkdir($dir, 02770);
}

$filename = "../../data/cos30018/messages.txt";
$statusfile = "../../data/cos30018/status.txt";
$errorfile = "../../data/cos30018/errors.txt";
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
if (isset($_POST["prompt"])) {
    $prompt = trim($_POST["prompt"]);
    if ($prompt != "") {
        // append user prmppt
        $handle = fopen($filename, "a");

        if ($handle) {
            fwrite($handle, "USER|" . $prompt . "\n");
            fclose($handle);
        }

        // SEND PROMPT TO MANAGER AGENT
        $command = "python3 managerAgent.py " . escapeshellarg($prompt);

        passthru($command);
    }
}

?>

<div class="container">

    <div class="left">

        <div class="header">
            Coding Agent
        </div>

        <div class="messages">
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

            <button type="submit">Send</button>

        </form>

    </div>


    <div class="right">

        <div class="header">
            Sandbox
        </div>
        <div class="project-status">

            <div class="project-title">
                <?php echo htmlspecialchars($projectTitle, ENT_QUOTES, "UTF-8"); ?>
            </div>

            <div class="project-stage">
                Stage:
                <strong>
                    <?php echo htmlspecialchars($currentStage, ENT_QUOTES, "UTF-8"); ?>
                </strong>
            </div>

            <div class="progress-container">

                <div
                    class="progress-bar"
                    style="width: <?php echo $progress; ?>%;"
                >
                </div>

            </div>

            <div class="progress-text">
                <?php echo $progress; ?>%
            </div>

        </div>
        <div class="sandbox">
            <iframe src="sandbox.html" style="width: 100%; height: 650px;"></iframe>
        </div>

        <div class="errors">
            <div class="errors-title">
                Errors
            </div>
            <div class="error-list">
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

</body>
</html>
