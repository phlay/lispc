(defun foobar (p)
  ( (lambda (t) t)
      ((lambda (x)  (if p "foo" "bar")) p)  ))

(defun main ()
  (test (foobar #t) "foo"))

