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
// create messages.txt if not exists
if (!file_exists($filename)) {
    $handle = fopen($filename, "w");
    if ($handle) {
        fwrite($handle, "AGENT|Hello! What would you like me to build?\n");
        fclose($handle);
    }
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

        <div class="sandbox">
            <iframe src="sandbox.html" style="width: 100%; height: 700px;"></iframe>
        </div>

    </div>

</div>

</body>
</html>