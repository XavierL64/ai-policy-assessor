# Assessment parameters
COMMITMENT_ID = "CP.1"
PDF_SOURCE = "policies/ABN/Exclusion list (Mar 2021).pdf"

# Run config
APPROACH = "two_step" # Choose from "single_step", "two_step_simple", "two_step"
MODEL_NAME = "gpt-4.1"
POLICY_DEBUG = False  # Set to True to print policy pages
INPUT_DEBUG = False   # Set to True to print other inputs
INTERACTIVE_MODE = False  # Set to True to manually select and edit commitment references (not applicable for single_step)

if __name__ == "__main__":
    print(f"\n{'='*80}")
    print(f"Running assessment with approach: {APPROACH.upper()}")
    print(f"Commitment: {COMMITMENT_ID}")
    print(f"Source: {PDF_SOURCE}")
    print(f"Model: {MODEL_NAME}")
    print(f"{'='*80}\n")

    if APPROACH == "single_step":
        from single_step import run_single_step_analysis
        result = run_single_step_analysis(
            commitment_id=COMMITMENT_ID,
            pdf_source=PDF_SOURCE,
            model_name=MODEL_NAME,
            policy_debug=POLICY_DEBUG,
            input_debug=INPUT_DEBUG,
            interactive_mode=INTERACTIVE_MODE
        )

    elif APPROACH == "two_step":
        from two_step import run_two_step_analysis
        result = run_two_step_analysis(
            commitment_id=COMMITMENT_ID,
            pdf_source=PDF_SOURCE,
            model_name=MODEL_NAME,
            policy_debug=POLICY_DEBUG,
            input_debug=INPUT_DEBUG,
            interactive_mode=INTERACTIVE_MODE
        )

    elif APPROACH == "two_step_simple":
        from two_step_simple import run_two_step_simple_analysis
        result = run_two_step_simple_analysis(
            commitment_id=COMMITMENT_ID,
            pdf_source=PDF_SOURCE,
            model_name=MODEL_NAME,
            policy_debug=POLICY_DEBUG,
            input_debug=INPUT_DEBUG,
            interactive_mode=INTERACTIVE_MODE
        )

    else:
        raise ValueError(f"Unknown approach: {APPROACH}. Must be 'single_step', 'two_step_simple', or 'two_step'")
