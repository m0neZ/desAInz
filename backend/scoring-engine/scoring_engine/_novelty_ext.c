#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <numpy/arrayobject.h>
#include <math.h>

static PyObject *compute_novelty(PyObject *self, PyObject *args) {
    PyArrayObject *embedding;
    PyArrayObject *centroid;
    if (!PyArg_ParseTuple(args, "O!O!", &PyArray_Type, &embedding, &PyArray_Type, &centroid)) {
        return NULL;
    }
    if (PyArray_NDIM(embedding) != 1 || PyArray_NDIM(centroid) != 1) {
        PyErr_SetString(PyExc_ValueError, "inputs must be 1-dimensional");
        return NULL;
    }
    if (PyArray_DIM(embedding, 0) != PyArray_DIM(centroid, 0)) {
        PyErr_SetString(PyExc_ValueError, "arrays must be of same length");
        return NULL;
    }
    npy_intp size = PyArray_DIM(embedding, 0);
    double *emb = (double *)PyArray_DATA(embedding);
    double *cen = (double *)PyArray_DATA(centroid);
    double dot = 0.0;
    double norm_e = 0.0;
    double norm_c = 0.0;
    for (npy_intp i = 0; i < size; ++i) {
        double e = emb[i];
        double c = cen[i];
        dot += e * c;
        norm_e += e * e;
        norm_c += c * c;
    }
    double norm = sqrt(norm_e) * sqrt(norm_c);
    if (norm == 0.0) {
        return PyFloat_FromDouble(0.0);
    }
    double result = 1.0 - dot / norm;
    return PyFloat_FromDouble(result);
}

static PyMethodDef Methods[] = {
    {"compute_novelty", compute_novelty, METH_VARARGS, "Compute novelty score."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef moduledef = {PyModuleDef_HEAD_INIT, "_novelty_ext", NULL, -1, Methods};

PyMODINIT_FUNC PyInit__novelty_ext(void) {
    import_array();
    return PyModule_Create(&moduledef);
}
