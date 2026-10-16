/* SPDX-License-Identifier: MIT
 * Reproducible 1080p offscreen GLES shader workload. No display is required.
 * This is a custom smoke/performance test, not a glmark2 score.
 */
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static double now(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

static GLuint shader(GLenum kind, const char *source) {
    GLuint s = glCreateShader(kind);
    glShaderSource(s, 1, &source, NULL);
    glCompileShader(s);
    GLint okay;
    glGetShaderiv(s, GL_COMPILE_STATUS, &okay);
    if (!okay) {
        char log[4096];
        glGetShaderInfoLog(s, sizeof(log), NULL, log);
        fprintf(stderr, "%s\n", log);
        exit(2);
    }
    return s;
}

int main(int argc, char **argv) {
    double duration = argc > 1 ? atof(argv[1]) : 8.0;
    if (duration < 1 || duration > 30) return 2;
    EGLDisplay display = eglGetPlatformDisplay(EGL_PLATFORM_SURFACELESS_MESA,
                                               EGL_DEFAULT_DISPLAY, NULL);
    if (!eglInitialize(display, NULL, NULL)) return 3;
    eglBindAPI(EGL_OPENGL_ES_API);
    const EGLint attrs[] = {EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT, EGL_RED_SIZE, 8,
        EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_NONE};
    EGLConfig config;
    EGLint count;
    if (!eglChooseConfig(display, attrs, &config, 1, &count) || count != 1) return 4;
    const EGLint surface_attrs[] = {EGL_WIDTH, 1920, EGL_HEIGHT, 1080, EGL_NONE};
    const EGLint context_attrs[] = {EGL_CONTEXT_CLIENT_VERSION, 3, EGL_NONE};
    EGLSurface surface = eglCreatePbufferSurface(display, config, surface_attrs);
    EGLContext context = eglCreateContext(display, config, EGL_NO_CONTEXT, context_attrs);
    if (!eglMakeCurrent(display, surface, surface, context)) return 5;
    const char *vertex = "#version 300 es\n"
        "void main(){vec2 p[3]=vec2[3](vec2(-1,-1),vec2(3,-1),vec2(-1,3));"
        "gl_Position=vec4(p[gl_VertexID],0,1);}";
    const char *fragment = "#version 300 es\nprecision highp float;"
        "uniform float phase; out vec4 color; void main(){"
        "vec2 p=gl_FragCoord.xy/vec2(1920,1080); float a=p.x+phase;"
        "for(int i=0;i<32;i++){a=fract(sin(a*3.13+p.y+float(i)*0.07)*4.17);}"
        "color=vec4(a,p.x,p.y,1);}";
    GLuint program = glCreateProgram();
    glAttachShader(program, shader(GL_VERTEX_SHADER, vertex));
    glAttachShader(program, shader(GL_FRAGMENT_SHADER, fragment));
    glLinkProgram(program);
    GLint okay;
    glGetProgramiv(program, GL_LINK_STATUS, &okay);
    if (!okay) return 6;
    glUseProgram(program);
    GLuint vao;
    glGenVertexArrays(1, &vao);
    glBindVertexArray(vao);
    glViewport(0, 0, 1920, 1080);
    GLint phase = glGetUniformLocation(program, "phase");
    for (int i = 0; i < 3; ++i) {
        glUniform1f(phase, i * .01f);
        glDrawArrays(GL_TRIANGLES, 0, 3);
        glFinish();
    }
    double start = now();
    unsigned frames = 0;
    do {
        glUniform1f(phase, frames * .001f);
        glDrawArrays(GL_TRIANGLES, 0, 3);
        glFinish();
        ++frames;
    } while (now() - start < duration);
    double elapsed = now() - start;
    unsigned char pixel[4] = {0};
    glReadPixels(960, 540, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, pixel);
    GLenum error = glGetError();
    printf("{\"renderer\":\"%s\",\"version\":\"%s\",\"width\":1920,"
           "\"height\":1080,\"shader_iterations\":32,\"frames\":%u,"
           "\"seconds\":%.6f,\"fps\":%.3f,\"sample_pixel\":[%u,%u,%u,%u],"
           "\"gl_error\":%u}\n", glGetString(GL_RENDERER), glGetString(GL_VERSION),
           frames, elapsed, frames / elapsed, pixel[0], pixel[1], pixel[2], pixel[3], error);
    eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    eglDestroyContext(display, context);
    eglDestroySurface(display, surface);
    eglTerminate(display);
    return error != GL_NO_ERROR || pixel[1] < 120 || pixel[1] > 135;
}
