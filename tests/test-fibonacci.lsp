(defun fibonacci (n)
  (if (le n 1)
    n
    (_fibonacci 2 1 1 n)))

(defun _fibonacci (k f_k f_k_1 n)
  (if (lt k n)
    (_fibonacci (inc k) (+ f_k f_k_1) f_k n)
    f_k))


(defun main ()
  (test (fibonacci 50) 12586269025))
