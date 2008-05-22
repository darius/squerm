(define (main)
  (print (eval '(cons 'a '()) safe-environment))
  (print (eval (test1) safe-environment)))

(define (test1)
  '(local 
    ((define (revappend xs ys)
       (if (null? xs)
           ys
           (revappend (cdr xs) (cons (car xs) ys)))))
    (revappend '(a b c) '(d))))
