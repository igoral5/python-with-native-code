#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <openssl/sha.h>
#include <math.h>
#include <stdbool.h>

static volatile bool working = true;

static PyObject *
mining_stop_working(PyObject *self, PyObject *args)
{
    working = false;
    Py_RETURN_NONE;
}

static PyObject *
mining_enable_working(PyObject *self, PyObject *args)
{
    working = true;
    Py_RETURN_NONE;
}

static size_t
get_max_length_value(unsigned long long n, size_t len_printable)
{
    return log(n) / log(len_printable) + 2;
}

static  size_t
get_value(const char *printable, unsigned long long n, char *value, size_t len_printable)
{
    n++;
    size_t i = 0;
    for(; n > 0; i++)
    {
        value[i] = printable[(n - 1) % len_printable];
        n = (n - 1) / len_printable;
    }
    return i;
}

static PyObject *
mining_mining(PyObject *self, PyObject *args)
{
    unsigned long long start, end;
    const char *init_value, *printable, *expected;
    size_t len_init_value, len_printable, len_expected;
    if (!PyArg_ParseTuple(args, "s#s#KKs#", &init_value, &len_init_value, &printable,
                          &len_printable, &start, &end, &expected, &len_expected))
        return NULL;
    char *value = PyMem_RawCalloc(1, get_max_length_value(end, len_printable));
    if (value == NULL)
        return PyErr_NoMemory();
    PyThreadState *_save;
    Py_UNBLOCK_THREADS
    SHA256_CTX initial_context, context;
    SHA256_Init(&initial_context);
    SHA256_Update(&initial_context, init_value, len_init_value);
    unsigned char hash[SHA256_DIGEST_LENGTH];
    char hexdigest[SHA256_DIGEST_LENGTH * 2 + 1];
    hexdigest[SHA256_DIGEST_LENGTH * 2] = '\0';
    for(; working && start < end; start++)
    {
        memcpy(&context, &initial_context, sizeof(SHA256_CTX));
        size_t len_value = get_value(printable, start, value, len_printable);
        SHA256_Update(&context, value, len_value);
        SHA256_Final(hash, &context);
        for(size_t i = 0; i < SHA256_DIGEST_LENGTH; i++)
        {
            sprintf(hexdigest + i * 2, "%02x", hash[i]);
        }
        if (strncmp(hexdigest, expected, len_expected) == 0)
        {
            Py_BLOCK_THREADS
            PyObject *res = Py_BuildValue("ssK", value, hexdigest, start);
            PyMem_RawFree(value);
            return res;
        }
    }
    Py_BLOCK_THREADS
    PyMem_RawFree(value);
    Py_RETURN_NONE;
}

static PyMethodDef mining_funcs[] = {
        {"mining", mining_mining, METH_VARARGS, "Search for special kinds of hash"},
        {"stop_working", mining_stop_working, METH_NOARGS, "Stop all search hash"},
        {"enable_working", mining_enable_working, METH_NOARGS, "Enable search hash"},
        {NULL, NULL, 0, NULL}
};

static struct PyModuleDef mining_module = {
        PyModuleDef_HEAD_INIT,
        "mining",   /* name of module */
        "Documentation for mining module", /* module documentation, may be NULL */
        -1,
        mining_funcs
};

PyMODINIT_FUNC
PyInit_mining(void)
{
    return PyModule_Create(&mining_module);
}

