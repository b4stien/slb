module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    watch: {
      coffeescript: {
        files: 'coffee/*.coffee',
        tasks: ["coffee"]
      }
    },
    coffee: {
      compile: {
        options: {
          bare: true
        },
        expand: true,
        flatten: true,
        cwd: 'coffee/',
        src: ['*.coffee'],
        dest: 'js',
        ext: '.js'
      },
    }
  });

  grunt.loadNpmTasks('grunt-contrib-coffee');
  grunt.loadNpmTasks('grunt-contrib-watch');

  grunt.registerTask('default', ['watch']);
};
