
<?php
header("Content-Type: application/json; charset=UTF-8");
header("Cache-Control: no-store");

$messagesFile = __DIR__ . "/messages.txt";
$statusFile = __DIR__ . "/status.txt";
$errorsFile = __DIR__ . "/errors.txt";

$status = [
    "title" => "New Project",
    "stage" => "Waiting for prompt",
    "progress" => 0
];

if (file_exists($statusFile)) {
    $lines = file($statusFile, FILE_IGNORE_NEW_LINES);

    foreach ($lines as $line) {
        $data = explode("|", $line, 2);

        if (count($data) < 2) {
            continue;
        }

        if ($data[0] == "TITLE") {
            $status["title"] = $data[1];
        } elseif ($data[0] == "STAGE") {
            $status["stage"] = $data[1];
        } elseif ($data[0] == "PROGRESS") {
            $status["progress"] = max(
                0,
                min(100, (int)$data[1])
            );
        }
    }
}

$messages = [];

if (file_exists($messagesFile)) {
    foreach (file($messagesFile, FILE_IGNORE_NEW_LINES) as $line) {
        $data = explode("|", $line, 2);

        if (count($data) == 2) {
            $messages[] = [
                "type" => $data[0],
                "message" => $data[1]
            ];
        }
    }
}

$errors = [];

if (file_exists($errorsFile)) {
    $errors = file(
        $errorsFile,
        FILE_IGNORE_NEW_LINES
    );
}

echo json_encode([
    "status" => $status,
    "messages" => $messages,
    "errors" => $errors
]);
?>
