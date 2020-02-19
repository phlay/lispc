(defun gcd (a b)
  (if (not (eq a 0)) (gcd (mod b a) a) b))

(defun main ()
  (test (gcd 77523602315 443794560949) 31))
