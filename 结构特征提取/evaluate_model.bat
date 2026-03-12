@echo off
REM 评估FCG分类器模型

python main_workflow_v2.py ^
    --source_dir "./test_cases" ^
    --output_dir "./output/evaluation" ^
    --label_file "./test_cases/labels.csv" ^
    --mode evaluate ^
    --classifier_model_path "./output/classifier/best_classifier.pth" ^
    --skip_training ^
    --cfg_model_path "./output/cfg_model.pth" ^
    --fcg_model_path "./output/fcg_model_final.pth"

pause
