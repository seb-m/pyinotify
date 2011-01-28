/*
  inotify_syscalls.c - native binding to inotify's syscalls
  Copyright (c) 2005-2011 Sebastien Martini <seb@dbzteam.org>

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in
  all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
  THE SOFTWARE.
*/
#include <Python.h>
#include <sys/syscall.h>

#if defined(__i386__)
#  define __NR_inotify_init		291
#  define __NR_inotify_add_watch	292
#  define __NR_inotify_rm_watch		293
#elif defined(__x86_64__)
# define __NR_inotify_init		253
# define __NR_inotify_add_watch		254
# define __NR_inotify_rm_watch		255
#elif (defined(__powerpc__) || defined(__powerpc64__))
# define __NR_inotify_init		275
# define __NR_inotify_add_watch		276
# define __NR_inotify_rm_watch		277
#elif defined (__ia64__)
# define __NR_inotify_init		1277
# define __NR_inotify_add_watch		1278
# define __NR_inotify_rm_watch		1279
#elif defined (__s390__)
# define __NR_inotify_init		284
# define __NR_inotify_add_watch		285
# define __NR_inotify_rm_watch		286
#elif defined (__alpha__)
# define __NR_inotify_init		444
# define __NR_inotify_add_watch 	445
# define __NR_inotify_rm_watch		446
#elif defined (__sparc__) || defined (__sparc64__)
# define __NR_inotify_init		151
# define __NR_inotify_add_watch		152
# define __NR_inotify_rm_watch		156
#elif defined (__arm__)
# define __NR_inotify_init		316
# define __NR_inotify_add_watch		317
# define __NR_inotify_rm_watch		318
#elif defined (__sh__)
# define __NR_inotify_init		290
# define __NR_inotify_add_watch		291
# define __NR_inotify_rm_watch		292
#elif defined (__sh64__)
# define __NR_inotify_init		318
# define __NR_inotify_add_watch		319
# define __NR_inotify_rm_watch		320
#elif defined (__hppa__)
# define __NR_inotify_init		269
# define __NR_inotify_add_watch		270
# define __NR_inotify_rm_watch		271
#elif defined (__mips__)
# define _MIPS_SIM_ABI32		1
# define _MIPS_SIM_NABI32		2
# define _MIPS_SIM_ABI64		3
# if _MIPS_SIM == _MIPS_SIM_ABI32
#  define __NR_Linux			4000
#  define __NR_inotify_init		(__NR_Linux + 284)
#  define __NR_inotify_add_watch	(__NR_Linux + 285)
#  define __NR_inotify_rm_watch		(__NR_Linux + 286)
# endif /* _MIPS_SIM == _MIPS_SIM_ABI32 */
# if _MIPS_SIM == _MIPS_SIM_ABI64
#  define __NR_Linux			5000
#  define __NR_inotify_init		(__NR_Linux + 243)
#  define __NR_inotify_add_watch	(__NR_Linux + 244)
#  define __NR_inotify_rm_watch		(__NR_Linux + 245)
# endif /* _MIPS_SIM == _MIPS_SIM_ABI64 */
# if _MIPS_SIM == _MIPS_SIM_NABI32
#  define __NR_Linux			6000
#  define __NR_inotify_init		(__NR_Linux + 247)
#  define __NR_inotify_add_watch	(__NR_Linux + 248)
#  define __NR_inotify_rm_watch		(__NR_Linux + 249)
# endif /* _MIPS_SIM == _MIPS_SIM_NABI32 */
#elif defined (__frv__)
# define __NR_inotify_init		291
# define __NR_inotify_add_watch		292
# define __NR_inotify_rm_watch		293
#elif defined (__parisc__)
# define __NR_Linux			0
# define __NR_inotify_init		(__NR_Linux + 269)
# define __NR_inotify_add_watch		(__NR_Linux + 270)
# define __NR_inotify_rm_watch		(__NR_Linux + 271)
#elif defined (__mc68000__)
# define __NR_inotify_init		284
# define __NR_inotify_add_watch		285
# define __NR_inotify_rm_watch		286
#else
# error "Unsupported architecture!"
#endif


static PyObject* inotify_init(PyObject* self, PyObject* args) {
  int result = -1;

  if (!PyArg_ParseTuple(args, ""))
    return NULL;

  result = syscall(__NR_inotify_init);
  if (result == -1) {
    PyErr_SetFromErrno(PyExc_IOError);
    return NULL;
  }

  return Py_BuildValue("i", result);
}

static PyObject* inotify_add_watch(PyObject* self, PyObject* args) {
  int fd = -1;
  char* name = NULL;
  unsigned int mask = 0;
  int result = -1;

  if(!PyArg_ParseTuple(args, "isI", &fd, &name, &mask))
    return NULL;

  result = syscall(__NR_inotify_add_watch, fd, name, mask);
  if (result == -1) {
    PyErr_SetFromErrno(PyExc_IOError);
    return NULL;
  }

  return Py_BuildValue("i", result);
}

static PyObject* inotify_rm_watch(PyObject* self, PyObject* args) {
  int fd = -1;
  unsigned int wd = 0;
  int result = -1;

  if(!PyArg_ParseTuple(args, "iI", &fd, &wd))
    return NULL;

  result = syscall(__NR_inotify_rm_watch, fd, wd);
  if (result == -1) {
    PyErr_SetFromErrno(PyExc_IOError);
    return NULL;
  }

  return Py_BuildValue("i", result);
}

static PyMethodDef inotify_syscalls_functions[] = {
  {"inotify_init", inotify_init, METH_VARARGS, "inotify initialization"},
  {"inotify_add_watch", inotify_add_watch, METH_VARARGS, "Add a new watch"},
  {"inotify_rm_watch", inotify_rm_watch, METH_VARARGS, "Remove a watch"},
  {0}
};

/* python 2 */
#if PY_VERSION_HEX < 0x03000000

void initinotify_syscalls(void) {
  Py_InitModule3("inotify_syscalls", inotify_syscalls_functions,
                 "module inotify_syscalls");
}

#else  /* python 3 */

static struct PyModuleDef inotify_syscallsmodule = {
  {}, /* m_base */
  "inotify_syscalls",  /* m_name */
  "module inotify_syscalls",  /* m_doc */
  0,  /* m_size */
  inotify_syscalls_functions,  /* m_methods */
  0,  /* m_reload */
  0,  /* m_traverse */
  0,  /* m_clear */
  0,  /* m_free */
};

PyObject* PyInit_inotify_syscalls(void) {
  return PyModule_Create(&inotify_syscallsmodule);
}

#endif  /* PY_VERSION_HEX */
