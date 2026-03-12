@echo off
REM 训练FCG分类器

python main_workflow_v2.py ^
    --source_dir "./test_cases" ^
    --output_dir "./output/classifier" ^
    --label_file "./test_cases/labels.csv" ^
    --mode train_classifier ^
    --fcg_model_path "./output/fcg_model_final.pth" ^
    --skip_training ^
    --cfg_model_path "./output/cfg_model.pth"

pause
