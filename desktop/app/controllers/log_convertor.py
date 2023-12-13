from app import schemas as s

from app.consts import OUTPUT_LOG_FILE_PATH, INPUT_LOG_FILE_PATH


def log_convertor():
    with open(INPUT_LOG_FILE_PATH, "r", encoding="utf-8") as i_f:
        with open(OUTPUT_LOG_FILE_PATH, "w") as o_f:
            line_no = 1
            try:
                for line in i_f:
                    log_line = s.LogLine.model_validate_json(line)
                    o_f.writelines(
                        [
                            f"{log_line.record.time.repr}:{log_line.record.module}:{log_line.record.level.name}:{log_line.record.message}",
                            "\n",
                        ]
                    )
                    line_no += 1
            except UnicodeDecodeError as e:
                print(f"Line {line_no} is not valid json. Error: {e}")
