const fs = require('fs');
const files = [
    './mock-ps.js',
    '../../../projects/framework-photoshop-js/utils.js',
    '../../../projects/framework-photoshop-js/event-constants.js',
    '../../../projects/framework-photoshop-js/events-core.js',
    '../../../projects/framework-photoshop-js/bootstrap.js',
];

let output = '';

files.forEach((file) => {
  output += fs.readFileSync(file, 'utf8');
});

fs.writeFileSync('./output.js', output);
