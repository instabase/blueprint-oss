import React from 'react';

// This is a little hacky. It can in principle mess stuff up if some other
// framework adds a :root CSS rule with --vars-that-end-with-color.

export default function useIntegerColors() {
  React.useEffect(() => {
    const newStyles: string[] = [];
    [...document.styleSheets].forEach(styleSheet => {
      [...(<any>styleSheet.cssRules)].forEach((rule: CSSStyleRule) => {
        if (rule.selectorText == ':root') {
          const style = rule.style;
          const newRuleLines: string[] = [];

          [...style].forEach(styleDeclaration => {
            const value = style.getPropertyValue(styleDeclaration).trim();
            const parsed = hexToRgb(value);
            if (styleDeclaration.startsWith('--') &&
                styleDeclaration.endsWith('-color') &&
                parsed != undefined)
            {
              const [r, g, b] = parsed;
              newRuleLines.push(
                `${styleDeclaration + '-integers'}: ` +
                parsed.map(n => n.toString()).join(', ') + ';');
            }
          });

          styleSheet.insertRule(
            ':root {\n' +
            newRuleLines.join('\n') +
            '}\n\n');
        }
      });
    });
  }, []);
}

function hexToRgb(hex: string): [number, number, number] | undefined {
  var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? [
    parseInt(result[1], 16),
    parseInt(result[2], 16),
    parseInt(result[3], 16),
  ] : undefined;
}
