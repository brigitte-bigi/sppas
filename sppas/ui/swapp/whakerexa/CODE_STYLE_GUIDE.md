# Code style guide for Javascript Programming Language

### General Guidelines

Code readability and reusability are top priorities. Code should be designed 
to be clear, maintainable, and generic to facilitate reuse across different 
contexts. Object-oriented programming (OOP) is strongly encouraged to 
structure and modularize the code effectively.  

All functions, methods, and classes must include well-written docstrings to 
document their purpose, parameters, and return values.

### Coding Rules

- **Use Object-Oriented Programming**: Encapsulate functionality in classes or modules. Avoid global variables.
- **Consistent Naming Convention**: 
  - Classes: PascalCase (e.g., `class DataManager`).
  - Functions, variables, and methods: camelCase (e.g., `fetchData`).
  - Constants: UPPER_SNAKE_CASE (e.g., `DEFAULT_TIMEOUT`).
- **Max Line Length**: Limit all lines to 119 characters.
- **Comments**: Write concise comments in American English. Explain the "why," not the "how."
- **Error Handling**: Provide feedback when objects or elements are not found. 
- **Explicit Comparisons**: Avoid implicit truthy or falsy comparisons. Example:

```javascript
// Correct:
if (items.length === 0) { /* handle empty case */ }
if (user === null) { /* handle null case */ }
if (isActive === true) { /* handle active case */ }

// Discouraged:
if (!items) { /* unclear */ }
if (user) { /* unclear */ }
if (isActive) { /* unclear */ }
```


#### Example of Bad Practice

Avoid writing code that is unclear, difficult to debug, or silently makes 
decisions, like this:

```javascript
// Wrong -- unclear logic, silent decisions:
document.querySelector('input[name="general_condition"]:checked')?.value === 'true' || true;
```

This code lacks readability, hides the logic behind the condition, and silently
defaults to true without notifying the user when the expected element is not 
found. Instead, you should explicitly handle the logic and provide feedback 
when issues occur:

```javascript
// Correct -- explicit logic, feedback provided if error:
let value = true;
const input = document.querySelector('input[name="general_condition"]:checked');

if (input === null) {
    console.error('Input not found: general_condition. Set to default: true.');
} else {
    ...
}
```

### Formating

- Use 4 spaces for indentation.
- Use single quotes (') unless double quotes are required.
- End statements with semicolons (;).
- Avoid hardcoding; use constants or configuration variables.
- Favor modular design with ES6 modules.
- Handle errors gracefully using try...catch blocks.
- Reuse code with generic, well-tested utilities.
- Leverage modern syntax (e.g., let, const, template literals, destructuring).


### Commenting and docstrings

Use JSDoc format for documentation. Write in American English. 
Use full sentences, starting with an uppercase letter and ending with a 
period. Explain why the code exists, not what it does (this should be clear 
from the code itself). Avoid over-commenting; instead, strive for clear and 
self-explanatory code.

Example of a well-documented function:

```javascript
/**
 * Fetch data from a given API endpoint.
 *
 * This function sends an HTTP GET request to the specified URL and
 * processes the JSON response. If the request fails, an error is logged.
 *
 * @param {string} url - The API endpoint to fetch data from.
 * @returns {Promise<Object>} The JSON response data.
 * 
 */
async function fetchData(url) {
...
}

```

### JavaScript Style Adaptations Explained

The author of Whakerexa has a visual impairment, and these rules improve code 
readability and accessibility. For the author, the following characters are 
visually impossible to distinguish: `{([`.

Therefore, avoid empty or visually ambiguous bracket-only expressions when a 
readable alternative exists.

Avoid:

```javascript
let value = ();   
```

Prefer explicit, named expressions:

```javascript
    let value = list();
```

The goal is not compact code.  
The goal is readable code.

