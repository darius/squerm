(define (main)
  (let ((keeper! (spawn #f keeper)))
    (spawn keeper!
           (lambda (? !)
             (print 'hello)
             whee))
    (spawn keeper!
           (lambda (? !)
             (print '"I am OK, though")
             (print 'hurray!)))))

(define (keeper ? !)
  (let loop ()
    (print (?))
    (loop)))
