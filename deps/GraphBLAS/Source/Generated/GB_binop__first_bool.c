//------------------------------------------------------------------------------
// GB_binop:  hard-coded functions for each built-in binary operator
//------------------------------------------------------------------------------

// SuiteSparse:GraphBLAS, Timothy A. Davis, (c) 2017-2019, All Rights Reserved.
// http://suitesparse.com   See GraphBLAS/Doc/License.txt for license.

//------------------------------------------------------------------------------

// If this file is in the Generated/ folder, do not edit it (auto-generated).

#include "GB.h"
#ifndef GBCOMPACT
#include "GB_control.h"
#include "GB_ek_slice.h"
#include "GB_binop__include.h"

// C=binop(A,B) is defined by the following types and operators:

// A+B function (eWiseAdd):    GB_AaddB__first_bool
// A.*B function (eWiseMult):  GB_AemultB__first_bool
// A*D function (colscale):    GB_AxD__first_bool
// D*A function (rowscale):    GB_DxB__first_bool

// C type:   bool
// A type:   bool
// B type:   bool
// BinaryOp: cij = aij

#define GB_ATYPE \
    bool

#define GB_BTYPE \
    bool

#define GB_CTYPE \
    bool

// aij = Ax [pA]
#define GB_GETA(aij,Ax,pA)  \
    bool aij = Ax [pA]

// bij = Bx [pB]
#define GB_GETB(bij,Bx,pB)  \
    ;

// cij = Ax [pA]
#define GB_COPY_A_TO_C(cij,Ax,pA) cij = Ax [pA] ;

// cij = Bx [pB]
#define GB_COPY_B_TO_C(cij,Bx,pB) cij = Bx [pB] ;

#define GB_CX(p) Cx [p]

// binary operator
#define GB_BINOP(z, x, y)   \
    z = x ;

// do the numerical phases of GB_add and GB_emult
#define GB_PHASE_2_OF_2

// hard-coded loops can be vectorized
#define GB_PRAGMA_VECTORIZE GB_PRAGMA_SIMD

// disable this operator and use the generic case if these conditions hold
#define GB_DISABLE \
    (GxB_NO_FIRST || GxB_NO_BOOL || GxB_NO_FIRST_BOOL)

//------------------------------------------------------------------------------
// C = A*D, column scale with diagonal D matrix
//------------------------------------------------------------------------------

GrB_Info GB_AxD__first_bool
(
    GrB_Matrix C,
    const GrB_Matrix A, bool A_is_pattern,
    const GrB_Matrix D, bool D_is_pattern,
    const int64_t *restrict kfirst_slice,
    const int64_t *restrict klast_slice,
    const int64_t *restrict pstart_slice,
    const int ntasks,
    const int nthreads
)
{ 
    #if GB_DISABLE
    return (GrB_NO_VALUE) ;
    #else
    bool *restrict Cx = C->x ;
    #include "GB_AxB_colscale_meta.c"
    return (GrB_SUCCESS) ;
    #endif
}

//------------------------------------------------------------------------------
// C = D*B, row scale with diagonal D matrix
//------------------------------------------------------------------------------

GrB_Info GB_DxB__first_bool
(
    GrB_Matrix C,
    const GrB_Matrix D, bool D_is_pattern,
    const GrB_Matrix B, bool B_is_pattern,
    int nthreads
)
{ 
    #if GB_DISABLE
    return (GrB_NO_VALUE) ;
    #else
    bool *restrict Cx = C->x ;
    #include "GB_AxB_rowscale_meta.c"
    return (GrB_SUCCESS) ;
    #endif
}

//------------------------------------------------------------------------------
// eWiseAdd: C = A+B or C<M> = A+B
//------------------------------------------------------------------------------

GrB_Info GB_AaddB__first_bool
(
    GrB_Matrix C,
    const GrB_Matrix M,
    const GrB_Matrix A,
    const GrB_Matrix B,
    const bool Ch_is_Mh,
    const int64_t *restrict C_to_M,
    const int64_t *restrict C_to_A,
    const int64_t *restrict C_to_B,
    const GB_task_struct *restrict TaskList,
    const int ntasks,
    const int nthreads
)
{ 
    #if GB_DISABLE
    return (GrB_NO_VALUE) ;
    #else
    #include "GB_add_template.c"
    return (GrB_SUCCESS) ;
    #endif
}

//------------------------------------------------------------------------------
// eWiseMult: C = A.*B or C<M> = A.*B
//------------------------------------------------------------------------------

GrB_Info GB_AemultB__first_bool
(
    GrB_Matrix C,
    const GrB_Matrix M,
    const GrB_Matrix A,
    const GrB_Matrix B,
    const int64_t *restrict C_to_M,
    const int64_t *restrict C_to_A,
    const int64_t *restrict C_to_B,
    const GB_task_struct *restrict TaskList,
    const int ntasks,
    const int nthreads
)
{ 
    #if GB_DISABLE
    return (GrB_NO_VALUE) ;
    #else
    #include "GB_emult_template.c"
    return (GrB_SUCCESS) ;
    #endif
}

#endif

