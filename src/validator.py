import re
import json
import os

class CodeValidator:
    def __init__(self, tokens_path):
        with open(tokens_path, 'r') as f:
            self.design_tokens = json.load(f)
        
    def validate_syntax(self, code):
        """Robust syntax check for Angular components."""
        errors = []
        
        # Check for matching brackets/parens/tags
        balanced_checks = [('{', '}'), ('[', ']'), ('(', ')'), ('<', '>')]
        for open_char, close_char in balanced_checks:
            if code.count(open_char) != code.count(close_char):
                # Simple check, ignoring strings/comments for this assessment
                errors.append(f"Mismatched characters: {open_char} and {close_char}")
            
        # Angular Specific Checks
        if "@Component" not in code:
            errors.append("Missing @Component decorator - required for Angular components.")
        
        if "selector:" not in code:
            errors.append("Component missing 'selector' definition.")
            
        if "template:" not in code and "templateUrl:" not in code:
            errors.append("Component missing 'template' or 'templateUrl'.")

        if errors:
            return False, " | ".join(errors)
        return True, "Syntax valid"

    def validate_tokens(self, code):
        """Check if colors and styles used are from the design tokens."""
        # Extract HEX codes from the code
        hex_colors = re.findall(r'#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}', code)
        
        allowed_colors = self._get_flattened_tokens(self.design_tokens['tokens']['colors'])
        
        errors = []
        for color in hex_colors:
            if color.lower() not in [c.lower() for c in allowed_colors.values()]:
                errors.append(f"Unauthorized color found: {color}. Use design tokens.")
        
        if errors:
            return False, "\n".join(errors)
        return True, "Tokens valid"

    def _get_flattened_tokens(self, obj, prefix=''):
        items = {}
        for k, v in obj.items():
            if isinstance(v, dict):
                items.update(self._get_flattened_tokens(v, f"{prefix}{k}-"))
            else:
                items[f"{prefix}{k}"] = v
        return items

    def full_validation(self, code):
        syntax_ok, syntax_msg = self.validate_syntax(code)
        if not syntax_ok:
            return False, syntax_msg
            
        tokens_ok, tokens_msg = self.validate_tokens(code)
        if not tokens_ok:
            return False, tokens_msg
            
        return True, "All checks passed"

if __name__ == "__main__":
    # Example usage
    validator = CodeValidator('design-tokens.json')
    test_code = """
    @Component({
      selector: 'app-login',
      template: '<div style="background: #6366f1">Login</div>'
    })
    export class LoginComponent {}
    """
    print(validator.full_validation(test_code))
