(defun foo (x y)
  ( (lambda (t) t) ((lambda (u v) (list x y u v)) x y) ))

(defun main ()
  (test (foo 3 5) '(3 5 3 5)))
