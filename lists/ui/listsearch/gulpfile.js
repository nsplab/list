/* dev environment setup
 */
var gulp = require('gulp');
var del = require('del');
var browserify = require('browserify');
var reactify = require('reactify'); // converts jsx to js
var source = require('vinyl-source-stream'); // converts strings to node.js streams
var buffer = require('vinyl-buffer');
var uglify = require('gulp-uglify');

var paths = {
    OUT: 'list_search.js',
    DEST_SRC: './static_js',
    ENTRY_POINT: './src/js/main.js'
};

gulp.task('clean:main', function() {
    return del([
        'static_js/list_search*.js'
    ]);
});

gulp.task('prod', function() {
    browserify({
        entries: [paths.ENTRY_POINT],
        transform: [reactify]
    })
        .bundle()
        .pipe(source(paths.OUT)) // gives streaming vinyl file object
        .pipe(buffer()) // convert from streaming to buffered vinyl file object
        .pipe(uglify()) // now uglify can operate on it
        .pipe(gulp.dest(paths.DEST_SRC))
    ;
});

gulp.task('dev', function() {
    browserify({
        entries: [paths.ENTRY_POINT],
        transform: [reactify],
        debug: true,
    })
        .bundle()
        .pipe(source(paths.OUT))
        .pipe(gulp.dest(paths.DEST_SRC))
    ;
});
gulp.task('build',['clean:main', 'prod']);
gulp.task('default',['clean:main', 'dev']);
