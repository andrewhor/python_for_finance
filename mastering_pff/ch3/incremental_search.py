""""
README
======
This file contains Python codes.
======
"""

""" An incremental search algorithm """
import pdb
import numpy as np

def incremental_search(f, a, b, dx):
    """
    :param f: The function to solve
    :param a: The left boundary x-axis value
    :param b: The right boundary x-axis value
    :param dx: The incremental value in searching
    :return: The x-axis value of the root,
                number of iterations used
    """
    fa = f(a)    
    c = a + dx 
    fc = f(c)    
    n = 1

    # Just keep moving from the min until you hit zero (aka, sign changes) and return that val
    # obviously very poor solution
    while np.sign(fa) == np.sign(fc):
        if a >= b:
            return a - dx, n
        
        a = c
        fa = fc
        c = a + dx
        fc = f(c)
        n += 1

    # edge cases where start points are roots
    if fa == 0:
        return a, n
    elif fc == 0:
        return c, n
    else:
        # assume mid point of a and c as answer
        return (a + c)/2., n

if __name__ == "__main__":
    """
    The keyword 'lambda' creates an anonymous function
    with input argument x
    """
    y = lambda x: x**3 + 2.0*x**2 - 5.
    root, iterations = incremental_search(y, -5., 5., 0.001)
    print("Root is:", root)
    print("Iterations:", iterations)