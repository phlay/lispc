(defun norm (x y)
  ( (lambda (sq) (+ (sq x) (sq y)))
      (lambda (x) (* x x)) ))

(defun main ()
  (test (norm 3 4) 25))
