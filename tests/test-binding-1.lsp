(defun foo (x y)
  ( (lambda (m) (+ x m)) (/ (- y x) 2) ))

(defun main ()
  (test (foo 3 15) 9))
